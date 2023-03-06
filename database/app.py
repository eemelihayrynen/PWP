import json
from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_restful import Api, Resource

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///moviesearch.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
api = Api(app)
db = SQLAlchemy(app)




@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(256), nullable=False)
    comments = db.Column(db.String(256), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    writer = db.Column(db.String(256), nullable=True)
    release_year = db.Column(db.Integer, nullable=True)
    genres = db.Column(db.String(256), nullable=True)
    actor_id = db.Column(db.Integer)
    director_id = db.Column(db.Integer)
    streaming_id = db.Column(db.Integer)


    actors = db.relationship("Actor", back_populates="in_movie")
    directors = db.relationship("Director", back_populates="in_movie_d")
    streamers = db.relationship("StreamingService", back_populates="streamingnow")

    def serialize(self):
         return {
                "title": self.title
            }



class Actor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    in_movie = db.relationship("Movie", back_populates="actors")


class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    in_movie_d = db.relationship("Movie", back_populates="directors")


class StreamingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    streamingnow = db.relationship("Movie", back_populates="streamers")


class MovieCollection(Resource):
    def get(self):
        Movie.serialize(Movie)
        return Movie.query.first()



    def post(self):
        return 400

"""
def populate_db():
    ctx.push()
    stream_1 = StreamingService(
        id=0,
        name = "Netflix"
    )
    actor_1=Actor(
        id=0,
        first_name = "Kate",
        last_name = "Winslet"


    )

    movie_1 = Movie(
        id = 0,
        title = "Titanic",
        comments = "Kys",
        rating = 7.9,
        writer = "Cameron",
        release_year = 1998,
        genres = "Romance"
       
        

    )
    movie_2 = Movie(
        id = 1,
        title = "Titanic2",
        comments = "Kys2",
        rating = 7.90,
        writer = "Cameron2",
        release_year = 19982,
        genres = "Romance2"
    
    )
    movie_3 = Movie(
        id = 2,
        title = "Titanic3",
        comments = "Kys3",
        rating = 7.900,
        writer = "Cameron3",
        release_year = 19983,
        genres = "Romance3"
    
        
    )
    with app.app_context():
        db.session.add(stream_1)
        db.session.add(actor_1)
        db.session.add(movie_1)
        db.session.add(movie_2)
        db.session.add(movie_3)

        db.session.commit()
    return 401
"""
api.add_resource(MovieCollection,"/ass/")


