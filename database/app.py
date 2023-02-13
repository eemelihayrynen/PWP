from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movieserach.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Movie(db.Model):
    id = 
    title = 
    director = 
    streaming_services = 
    actors = 
    rating =
    writer =
    release_year = 
    genres =

class Actor(db.Model):
    id =
    first_name =
    last_name =
    movie_id =

class Director(db.Model):
    id =
    first_name =
    last_name =
    movie_id =

class StreamingService(db.Model):
    id =
    name =