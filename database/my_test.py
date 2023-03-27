import os
import pytest
import tempfile
import app
from app import Movie, Actor, Director, StreamingService

from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def db_handle():
    print("ass")
    db_fd, db_fname = tempfile.mkstemp()
    app.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.app.config["TESTING"] = True
    with app.app.app_context():
        app.db.create_all()
    yield app.db
    app.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _get_film():
    title= "The Dark Knight"
    comments= ""
    rating= 9.0
    writer= "David S. Goyer"
    release_year= 2008
    genres= "Action/Drama/Crime"
    return Movie(
            title=title, comments=comments, rating=rating, writer=writer, release_year=release_year, genres=genres, actors=[]
            )

def test_add_film(db_handle):
    movie = _get_film()
    db_handle.session.add(movie)
    db_handle.session.commit()
    print("success")
    assert Movie.query.count() == 1
    