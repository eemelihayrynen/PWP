import json
from flask import Flask, Response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_restful import Api, Resource
from marshmallow import Schema, fields

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
    def get(self,moviename):
        db_movie = Movie.query.filter_by(title = moviename).first()
        db_movie_dict = db_movie.__dict__
        del db_movie_dict['_sa_instance_state']
        return jsonify(db_movie_dict)
    
    def delete(self,moviename):
        pass

class MovieAddition(Resource):
    def post(self):
        id = int(request.json["id"])
        title = str(request.json["title"])
        comments = str(request.json["comments"])
        rating = float(request.json["rating"])
        writer = str(request.json["writer"])
        release_year = int(request.json["release_year"])
        genres = str(request.json["genres"])
        movie = Movie(
            id=id, title=title, comments=comments, rating=rating, writer=writer, release_year=release_year, genres=genres
        )
        db.session.add(movie)
        db.session.commit()
        resp =Response()
        resp.status=201
        return resp
    
class ActorAddition(Resource):
    def post(self):
        id = int(request.json["id"])
        first = str(request.json["first_name"])
        last = str(request.json["last_name"])
        actor = Actor(
            id=id, first_name=first, last_name=last
        )
        db.session.add(actor)
        db.session.commit()
        resp =Response()
        resp.status=201
        return resp
    
class ActorCollection(Resource):    
    def delete(self,actorname):
        pass
    def get(self,actorname):
        pass

class StreamingCollection(Resource):
    def put(self,moviename):
        pass

api.add_resource(MovieCollection,"/Moviesearch/<moviename>/")
api.add_resource(MovieAddition,"/Movie/")
api.add_resource(ActorAddition,"/Actorsearch/<actorname>/")
api.add_resource(ActorCollection,"/Actor/")
api.add_resource(StreamingCollection,"/Streaming/<moviename>/")
