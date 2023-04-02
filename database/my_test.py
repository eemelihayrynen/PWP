import json
import os
import pytest
import tempfile
from app import *
from app import Movie, Actor, Director, StreamingService
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.config["TESTING"] = True

    db.create_all()
    _populate_db()

    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _populate_db():
    for i in range(1,3):
        movie = Movie(title="movie {}".format(i), comments="comments", rating=i, writer="writer", release_year=i, genres="action", actors=[])
        db.session.add(movie)
        actor = Actor(first_name = "Daniel", last_name=str(i))
        db.session.add(actor)
    db.session.commit()

"""

def test_add_film(client):
    movie = _get_film()
    client.session.add(movie)
    client.session.commit()
    print("success")
    assert Movie.query.count() == 1
"""
def _get_film():
    title= "The Dark Knight"
    comments= ""
    rating= 9.0
    writer= "David S. Goyer"
    release_year= 2008
    genres= "Action/Drama/Crime"
    directors = "Chris Nolan"
    streamingServices = "HBO Max"
    return {"title": title, "comments":comments, "rating":rating, "writer":writer, "release_year":release_year, "genres":genres, "actors":[{"first_name":"Daniel","last_name":"Craig"}]
            ,"directors":[{"first_name":"Daniel","last_name":"Craig"}], "streaming_services": [{"name": "Netflix"}] }

class Testing(object):
    MOVIE_URL = "/movie/movie 1/"
    ACTOR_URL = "/actor/Daniel 1/"
    MOVIE_POST_URL = "/movie/"
    ACTOR_POST_URL = "/actor/"
    MOVIE_URL2 = "/movie/movie 2/"
    ACTOR_URL2 = "/actor/Daniel 2/"
    def test_get_film(self,client):
        """
        tests get method for movie, returns 200 when correct also tests the length of the data
        """
        resp = client.get(self.MOVIE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 9 #there are 9 categories of data in a movie
        assert body["title"]

    def test_delete_film(self,client):
        """
        tests delete method for movie, returns 200 when correct and also tests after if movie is really gone and returns not found 404
        """
        resp = client.delete(self.MOVIE_URL)
        assert resp.status_code == 200
        resp = client.get(self.MOVIE_URL)
        assert resp.status_code == 404

    def test_get_actor(self,client):
        """
        tests get method for actor, returns 200 when correct also tests the length of the data
        """
        resp = client.get(self.ACTOR_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 2 #there are 2 categories of data in a actor
        assert body["first_name"]

    def test_delete_actor(self,client):
        """
        tests delete method for actor, returns 200 when correct and also tests after if actor is really gone and returns not found 404
        """
        resp = client.delete(self.MOVIE_URL)
        assert resp.status_code == 200
        resp = client.get(self.MOVIE_URL)
        assert resp.status_code == 404

    def test_add_movie(self,client):
        """
        tests post method for movie
        """
        m = _get_film()
        resp = client.post(self.MOVIE_POST_URL,json = m)
        assert resp.status_code == 201

    def test_add_actor(self,client):
        """
        tests post method for actor
        """
        a = {"first_name":"Daniel","last_name":"Craig"}
        resp = client.post(self.ACTOR_POST_URL,json = a)
        assert resp.status_code == 201

    def test_edit_movie(self,client):
        """
        tests put method for movie
        """
        m = _get_film()
        resp = client.post(self.MOVIE_URL2,json = m)
        assert resp.status_code == 204

    def test_edit_actor(self,client):
        """
        tests put method for movie
        """
        a = {"first_name":"Daniel","last_name":"Craig"}
        resp = client.post(self.MOVIE_URL2,json = a)
        assert resp.status_code == 204
