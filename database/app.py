import json
from flask import Flask, Response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_restful import Api, Resource
#from marshmallow import Schema, fields
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType


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


MovieActorsAssociation = db.Table('MovieActorsAssosiation',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('actor_id', db.Integer, db.ForeignKey('actor.id'), primary_key=True)
)

MovieDirectorsAssociation = db.Table('MovieDirectorsAssosiation',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('director_id', db.Integer, db.ForeignKey('director.id'), primary_key=True)
)

MovieStreamingServicesAssociation = db.Table('MovieStreamingServicesAssosiation',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('streaming_service_id', db.Integer, db.ForeignKey('streaming_service.id'), primary_key=True)
)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(256), nullable=False)
    comments = db.Column(db.String(256), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    writer = db.Column(db.String(256), nullable=True)
    release_year = db.Column(db.Integer, nullable=True)
    genres = db.Column(db.String(256), nullable=True)
    #actor_id = db.Column(db.Integer, db.ForeignKey(actor.id))
    #pp director_id = db.Column(db.Integer)
    #pp streaming_id = db.Column(db.Integer)

    actors = db.relationship("Actor", secondary=MovieActorsAssociation, back_populates='movies')
    directors = db.relationship("Director", secondary=MovieDirectorsAssociation, back_populates='movies')
    streaming_services = db.relationship("StreamingService", secondary=MovieStreamingServicesAssociation, back_populates='movies')

    def serialize(self):
        actors = []
        #TODO: convert these loops to shorter code e.g. with list comprehension
        for a in self.actors:
            actors.append(a.serialize())
        directors = []
        for d in self.directors:
            directors.append(d.serialize())
        streaming_services = []
        for s in self.streaming_services:
            streaming_services.append(s.serialize())
        return {
            "title": self.title,
            "comments": self.comments,
            "rating": self.rating,
            "writer": self.writer,
            "release_year": self.release_year,
            "genres": self.genres,
            "actors": actors,
            "directors": directors,
            "streaming_services": streaming_services,
        }
    
    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["title"] #TODO: decide if actors, etc. are required and match to db definitions
        }
        props = schema["properties"] = {}
        props["title"] = {
            "description": "Name of the movie",
            "type": "string"
        }
        props["comments"] = {
            "description": "Comments in one string",
            "type": "string"
        }
        props["rating"] = {
            "description": "Rating from imdb",
            "type": "number"
        }
        props["writer"] = {
            "description": "Writer",
            "type": "string"
        }
        props["release_year"] = {
            "description": "Year of the original release",
            "type": "integer"
        }
        props["genres"] = {
            "description": "Genres in one string",
            "type": "string"
        }
        props["actors"] = {
            "description": "List of actors",
            "$def": "#Actor.json_schema()"#TODO: this reference doesn't work
        }
        props["directors"] = {
            "description": "List of directors",
            "$def": "#Director.json_schema()"#TODO: this reference doesn't work
        }
        props["streaming_services"] = {
            "description": "List of streaming services",
            "$def": "#StreamingService.json_schema()"#TODO: this reference doesn't work
        }
        return schema

class Actor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    #movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    #in_movie = db.relationship("Movie", back_populates="actors")
    
    movies = db.relationship("Movie", secondary=MovieActorsAssociation, back_populates='actors')

    def serialize(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name
        }
        
    @staticmethod
    def json_schema():
        schema = {
            "$id": "/schemas/actor",
            "type": "object",
            "required": ["first_name", "last_name"]
        }
        props = schema["properties"] = {}
        props["first_name"] = {
            "description": "First name",
            "type": "string"
        }
        props["last_name"] = {
            "description": "Last name",
            "type": "string"
        }
        return schema

class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    #pp movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    #pp in_movie_d = db.relationship("Movie", back_populates="directors")

    movies = db.relationship("Movie", secondary=MovieDirectorsAssociation, back_populates='directors')

    def serialize(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name
        }

    @staticmethod
    def json_schema():
        schema = {
            "$id": "/schemas/director",
            "type": "object",
            "required": ["first_name", "last_name"]
        }
        props = schema["properties"] = {}
        props["first_name"] = {
            "description": "First name",
            "type": "string"
        }
        props["last_name"] = {
            "description": "Last name",
            "type": "string"
        }
        return schema

class StreamingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    #pp movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    #pp streamingnow = db.relationship("Movie", back_populates="streamers")

    movies = db.relationship("Movie", secondary=MovieStreamingServicesAssociation, back_populates='streaming_services')

    def serialize(self):
        return {
            "name": self.name,
        }
    
    @staticmethod
    def json_schema():
        schema = {
            "$id": "/schemas/streaming_services",
            "type": "object",
            "required": ["name"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Name of the service",
            "type": "string"
        }
        return schema


class MovieCollection(Resource):
    def get(self, moviename):
        db_movie = Movie.query.filter_by(title = moviename).first()

        #db_movie_dict = db_movie.__dict__
        #del db_movie_dict['_sa_instance_state']
        return db_movie.serialize()
    
    def delete(self,moviename):
        pass

class MovieAddition(Resource):
    def post(self):
        validator = Draft7Validator(
                Movie.json_schema(),
                format_checker=Draft7Validator.FORMAT_CHECKER
                )
        try:
            print("Trying to validate request json")
            validator.validate(request.json)
        except ValidationError as error_message:
            raise BadRequest(description=str(error_message))
        
        #TODO: create deserialize method to Movie class to simplify this
        title = str(request.json["title"])
        comments = str(request.json["comments"])
        rating = float(request.json["rating"])
        writer = str(request.json["writer"])
        release_year = int(request.json["release_year"])
        genres = str(request.json["genres"])
        to_be_checked_actors = list(request.json["actors"])
        to_be_checked_directors = list(request.json["directors"])
        to_be_checked_streaming_services = list(request.json["streaming_services"])
        #TODO: check that the movie doesn't exist yet.
        movie = Movie(
            title=title, comments=comments, rating=rating, writer=writer, release_year=release_year, genres=genres, actors=[]
        )
        #print(to_be_checked_actors)
        for actor in to_be_checked_actors:
            print(actor)
            db_actor = Actor.query.filter_by(first_name = actor["first_name"],last_name = actor["last_name"]).first()
            if db_actor == None:
                #no actor found, so let's add a new one
                print("Actor not in database")
                movie.actors.append(
                    Actor(
                        first_name=actor["first_name"], last_name=actor["last_name"]
                        )
                )
            else:
                #if the actor existed, we'll add refrerence to the existing entry
                movie.actors.append(db_actor)
        
        for director in to_be_checked_directors:
            print(director)
            db_director = Director.query.filter_by(first_name = director["first_name"],last_name = director["last_name"]).first()
            if db_director == None:
                #no director found, so let's add a new one
                print("Director not in database")
                movie.directors.append(
                    Director(
                        first_name=director["first_name"], last_name=director["last_name"]
                        )
                )
            else:
                #if the actor existed, we'll add refrerence to the existing entry
                movie.director.append(db_director)

        for streaming_service in to_be_checked_streaming_services:
            print(streaming_service)
            db_streaming_service = StreamingService.query.filter_by(name = streaming_service["name"]).first()
            if db_streaming_service == None:
                #no streaming_service found, so let's add a new one
                print("streaming_service not in database")
                movie.streaming_services.append(
                    StreamingService(
                        name=streaming_service["name"]
                        )
                )
            else:
                #if the actor existed, we'll add refrerence to the existing entry
                movie.streaming_services.append(db_streaming_service)

        db.session.add(movie)
        db.session.commit()
        resp =Response()
        resp.status=201
        #TODO: add uri of created movie to the response
        return resp
    
class ActorAddition(Resource):
    def post(self):

        first = str(request.json["first_name"])
        last = str(request.json["last_name"])
        actor = Actor(
            first_name=first, last_name=last
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
        db_actor = Actor.query.filter_by(first_name = actorname.split(" ")[0],last_name = actorname.split(" ")[1]).first()
        db_actor_dict = db_actor.__dict__
        del db_actor_dict['_sa_instance_state']
        return jsonify(db_actor_dict)


class StreamingCollection(Resource):
    def put(self,moviename):
        pass

api.add_resource(MovieCollection,"/Moviesearch/<moviename>/")
api.add_resource(MovieAddition,"/Movie/")
api.add_resource(ActorAddition,"/Actorsearch/<actorname>/")
api.add_resource(ActorCollection,"/Actor/")
api.add_resource(StreamingCollection,"/Streaming/<moviename>/")

