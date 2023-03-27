import json
from flask import Flask, Response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from flask_restful import Api, Resource
#from marshmallow import Schema, fields
from jsonschema import validate, ValidationError, Draft7Validator
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from werkzeug.routing import BaseConverter
from flasgger import Swagger, swag_from



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///moviesearch.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SWAGGER"] = {
    "title": "Sensorhub API",
    "openapi": "3.0.3",
    "uiversion": 3,
}
api = Api(app)
db = SQLAlchemy(app)
swagger = Swagger(app, template_file="doc/moviesearch.yml")

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
    db.Column(
        'streaming_service_id',
        db.Integer, db.ForeignKey('streaming_service.id'),
        primary_key=True
    )
)

class Movie(db.Model):
    """Database definition and utility functions for streaming movies"""
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(256), nullable=False)
    comments = db.Column(db.String(256), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    writer = db.Column(db.String(256), nullable=True)
    release_year = db.Column(db.Integer, nullable=True)
    genres = db.Column(db.String(256), nullable=True)

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
    
    def deserialize(self, doc):
        #TODO a way to desearialize actors, directors, streamingservices
        # 
        # for a in doc["actors"]:
        #   a.deserialize()
        #   


        self.id = doc["id"]
        self.title =doc["title"]
        self.comments = doc["comments"]
        self.rating = doc["rating"]
        self.writer = doc["writer"]
        self.release_year = doc["release_year"]
        self.genres = doc["genres"]
    
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
    """Database definition and utility functions for actors"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    
    movies = db.relationship("Movie", secondary=MovieActorsAssociation, back_populates='actors')

    def serialize(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name
        }
    
    def deserialize(self, doc):
        self.first_name = doc["first_name"]
        self.last_name = doc["last_name"]
        
        
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
    """Database definition and utility functions for director"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)

    movies = db.relationship("Movie", secondary=MovieDirectorsAssociation, back_populates='directors')

    def serialize(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name
        }
    
    def deserialize(self, doc):
        self.first_name = doc["first_name"]
        self.last_name = doc["last_name"]


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
    """Database definition and utility functions for streaming services"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    movies = db.relationship("Movie", secondary=MovieStreamingServicesAssociation, back_populates='streaming_services')

    def serialize(self):
        return {
            "name": self.name,
        }
    
    def deserialize(self, doc):
        self.name = doc["name"]
    
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
    
class MovieConverter(BaseConverter):
    def to_python(self, value):
        db_movie = Movie.query.filter_by(title=value).first()
        if db_movie is None:
            raise NotFound
        return db_movie
        
    def to_url(self, value):
        return value.title
class MovieItem(Resource):
    """Resource for getting (searching) existing movie or modifying it."""
    def get(self, movie):
        """
        Get a movie with title
        ---
        description: Get a movie by title
        parameters:
        - $ref: '#/components/parameters/movie'
        responses:
            '200':
                description: Got movie details successfully
                content:
                    application/JSON:
                        schema:
                            $ref: '#/components/schemas/Movie'
                        example:
                            title: The Lord of the Rings The Fellowship of the Ring
                            comments: Very good. I like.
                            rating: 10
                            writer: Fran Walsh, Philippa Boyens
                            release_year: 2001
                            genres: Fantasy
                            actors:
                                - first_name: Elijah
                                  last_name: Wood
                                - first_name: Ian
                                  last_name: McKellen
                            directors:
                                - first_name: Peter
                                  last_name: Jackson
                            streaming_services:
                                - name: HBO Max
            '404':
                description: Movie was not found from server
        """
        #db_movie = Movie.query.filter_by(title = moviename).first()

        #db_movie_dict = db_movie.__dict__
        #del db_movie_dict['_sa_instance_state']
        return movie.serialize()
    
    def delete(self,movie):
        #movie = db.session.query(Movie).filter(Movie.title == moviename).first()
        db.session.delete(movie)
        db.session.commit()

    def put(self, movie):
        """Modify existing movie"""
        #TODO TEST THIS METHOD

        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Movie.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        movie.deserialize(request.json)
        try:
            db.session.add(movie)
            db.session.commit()
        
        except IntegrityError:
            raise Conflict(
                409,
                description="Identical movie already exists.".format(
                **request.json
                )
            )

        return Response(status=204)

class MovieCollection(Resource):
    """Resource for getting all movies or adding a new."""
    def post(self):
        """
        Method to post a new movie to the db
        ---
        description: Post a new movie
        requestBody:
            description: JSON formatted data
            content:
                application/JSON:
                    schema:
                        $ref: '#/components/schemas/Movie'
                    example:
                        title: The Lord of the Rings The Fellowship of the Ring
                        comments: Very good. I like.
                        rating: 10
                        writer: Fran Walsh, Philippa Boyens
                        release_year: 2001
                        genres: Fantasy
                        actors:
                            - first_name: Elijah
                              last_name: Wood
                            - first_name: Ian
                              last_name: McKellen
                        directors:
                            - first_name: Peter
                              last_name: Jackson
                        streaming_services:
                            - name: HBO Max
        responses:
            '201':
                description: Movie added successfully
                headers:
                    Location:
                        description: URI of the movie added
                        schema:
                            type: string
                        
        """#TODO: add error responses once they are added to the method itself
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
            print("ass")
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
                movie.directors.append(db_director)

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
        return Response(status=201, headers={"Location": api.url_for(MovieItem, movie=movie)})
    
class ActorCollection(Resource):
    """Resource for getting all actors and adding new."""
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
    
class ActorItem(Resource):
    """Resource for getting and modifying existing actor."""    
    def delete(self,actorname):
        actor = db.session.query(Actor).filter(Actor.first_name == actorname.split(" ")[0],Actor.last_name == actorname.split(" ")[1]).first()
        db.session.delete(actor)
        db.session.commit()
    
    def get(self,actorname):
        db_actor = Actor.query.filter_by(first_name = actorname.split(" ")[0],last_name = actorname.split(" ")[1]).first()
        db_actor_dict = db_actor.__dict__
        del db_actor_dict['_sa_instance_state']
        return jsonify(db_actor_dict)

    def put(self, actorname):
        #TODO TEST THIS METHOD

        """
        Edit existing actor
        """

        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Actor.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        actorname.deserialize(request.json)
        try:
            db.session.add(actorname)
            db.session.commit()
        
        except IntegrityError:
            raise Conflict(
                409,
                description="Identical actor already exists.".format(
                **request.json
                )
            )
        return Response(status=204)

class StreamingCollection(Resource):
    def put(self,streamingservice):
        
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, StreamingService.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        streamingservice.deserialize(request.json)
        try:
            db.session.add(streamingservice)
            db.session.commit()
        
        except IntegrityError:
            raise Conflict(
                409,
                description="Identical streamingservice already exists.".format(
                **request.json
                )
            )
        return Response(status=204)
        

app.url_map.converters["movie"] = MovieConverter
api.add_resource(MovieItem,"/movie/<movie:movie>/") 
api.add_resource(MovieCollection,"/movie/")
api.add_resource(ActorCollection,"/actor/")
api.add_resource(ActorItem,"/actor/<actorname>/")
api.add_resource(StreamingCollection,"/streaming/<movie:movie>/")
