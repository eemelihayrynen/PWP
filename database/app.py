'''
Main code for our Movie search API
Sources for code:
https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/
https://github.com/enkwolf/pwp-course-sensorhub-api-example
'''
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
    __table_args__ = (
        db.UniqueConstraint("title", "release_year"),
    )
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(256), nullable=False)
    comments = db.Column(db.String(256), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    writer = db.Column(db.String(256), nullable=True)
    release_year = db.Column(db.Integer, nullable=True)
    genres = db.Column(db.String(256), nullable=True)

    actors = db.relationship("Actor", secondary=MovieActorsAssociation, back_populates='movies')
    directors = db.relationship(
        "Director",
        secondary=MovieDirectorsAssociation,
        back_populates='movies'
        )
    streaming_services = db.relationship(
        "StreamingService",
        secondary=MovieStreamingServicesAssociation,
        back_populates='movies'
        )

    def serialize(self, short_form=False):
        '''Serialize function for Movie resource'''
        if short_form:
            return {"title": self.title}

        actors = []
        #TODO: convert these loops to shorter code e.g. with list comprehension
        for actor in self.actors:
            actors.append(actor.serialize())
        directors = []
        for director in self.directors:
            directors.append(director.serialize())
        streaming_services = []
        for streaming_service in self.streaming_services:
            streaming_services.append(streaming_service.serialize(short_form=True))
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
        '''De-serialize function for Movie resource'''
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
        '''JSON schema function for Movie schema validation'''
        schema = {
            "type": "object",
            "required": ["title"]
            #TODO: decide if actors, etc. are required and match to db definitions
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
            "type": "array",
            "items": Actor.json_schema()
        }
        props["directors"] = {
            "description": "List of directors",
            "type": "array",
            "items": Director.json_schema()
        }
        props["streaming_services"] = {
            "description": "List of streaming services",
            "type": "array",
            "items": StreamingService.json_schema()
        }
        return schema

class Actor(db.Model):
    """Database definition and utility functions for actors"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)

    movies = db.relationship("Movie", secondary=MovieActorsAssociation, back_populates='actors')

    def serialize(self):
        '''Serialize function for Actor resource'''
        return {
            "first_name": self.first_name,
            "last_name": self.last_name
        }

    def deserialize(self, doc):
        '''De-serialize function for Actor resource'''
        self.first_name = doc["first_name"]
        self.last_name = doc["last_name"]

    @staticmethod
    def json_schema():
        '''JSON schema function for Actor schema validation'''
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

    movies = db.relationship(
        "Movie",
        secondary=MovieDirectorsAssociation,
        back_populates='directors'
        )

    def serialize(self):
        '''Serialize function for Director resource'''
        return {
            "first_name": self.first_name,
            "last_name": self.last_name
        }

    def deserialize(self, doc):
        '''De-serialize function for Director resource'''
        self.first_name = doc["first_name"]
        self.last_name = doc["last_name"]

    @staticmethod
    def json_schema():
        '''JSON schema function for Director schema validation'''
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

    movies = db.relationship(
        "Movie",
        secondary=MovieStreamingServicesAssociation,
        back_populates='streaming_services'
        )

    def serialize(self, short_form=False):
        '''Serialize function for StreamingService resource'''
        if short_form:
            return {"name": self.name}
        movies = []
        for movie in self.movies:
            movies.append(movie.serialize(short_form=True))
        return {
            "name": self.name,
            "movies": movies
        }

    def deserialize(self, doc):
        '''De-serialize function for StreamingService resource'''
        self.name = doc["name"]

    @staticmethod
    def json_schema():
        '''JSON schema function for StreamingService schema validation'''
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
    '''Helper class to get Movie from url and url from Movie'''
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
        """
        Method for deleting a movie
        ---
        description: Delete movie by name
        parameters:
          - $ref: '#/components/schemas/Movie'
        responses:
            '204':
                description: Deleted movie successfully
            '404':
                description: Movie was not found
        """
        #movie = db.session.query(Movie).filter(Movie.title == moviename).first()
        db.session.delete(movie)
        db.session.commit()

    def put(self, movie):
        """
        Modify existing movie
        ---
        description: Edit movie in the database
        parameters:
          - $ref: '#/components/schemas/movie'
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
            '204':
                description: Movie modified successfully
                headers:
                    Location:
                        description: URI of the movie modified
                        schema:
                            type: string
            '409':
                description: Identical Movie exists
            '404':
                description: Movie was not found
        """
        #TODO TEST THIS METHOD

        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json,Movie.json_schema())
        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e

        movie.title = str(request.json["title"])
        movie.comments = str(request.json["comments"])
        movie.rating = float(request.json["rating"])
        movie.writer = str(request.json["writer"])
        movie.release_year = int(request.json["release_year"])
        movie.genres = str(request.json["genres"])
        to_be_checked_actors = list(request.json["actors"])
        to_be_checked_directors = list(request.json["directors"])
        to_be_checked_streaming_services = list(request.json["streaming_services"])

        for actor in to_be_checked_actors:
            print(actor)
            db_actor = Actor.query.filter_by(
                first_name = actor["first_name"],
                last_name = actor["last_name"]
                ).first()
            if db_actor is None:
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
            db_director = Director.query.filter_by(
                first_name = director["first_name"],
                last_name = director["last_name"]
                ).first()
            if db_director is None:
                #no director found, so let's add a new one
                print("Director not in database")
                movie.directors.append(
                    Director(
                        first_name=director["first_name"], last_name=director["last_name"]
                        )
                )
            else:
                #if the director existed, we'll add refrerence to the existing entry
                movie.directors.append(db_director)

        for streaming_service in to_be_checked_streaming_services:
            print(streaming_service)
            db_streaming_service = StreamingService.query.filter_by(
                name = streaming_service["name"]
                ).first()
            if db_streaming_service is None:
                #no streaming_service found, so let's add a new one
                print("streaming_service not in database")
                movie.streaming_services.append(
                    StreamingService(
                        name=streaming_service["name"]
                        )
                )
            else:
                #if the streaming_service existed, we'll add refrerence to the existing entry
                movie.streaming_services.append(db_streaming_service)
        try:
            db.session.add(movie)
            db.session.commit()

        except IntegrityError as i_e:
            raise Conflict(description="Identical movie already exists.") from i_e

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
            '400':
                description: Bad request/Invalid JSON Schema
            '409':
                description: Identical Movie exists
                        
        """#TODO: add error responses once they are added to the method itself
        try:
            #DOC:If the request content type is not ``application/json``, this
            # will raise a 400 Bad Request error.
            request.json
        except BadRequest as b_r:
            raise UnsupportedMediaType(description="UnsupportedMediaType, JSON document required.") from b_r
        validator = Draft7Validator(
                Movie.json_schema(),
                format_checker=Draft7Validator.FORMAT_CHECKER
                )
        try:
            print("Trying to validate request json")
            validator.validate(request.json)

        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e

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
            title=title,
            comments=comments,
            rating=rating,
            writer=writer,
            release_year=release_year,
            genres=genres,
            actors=[]
        )
        #print(to_be_checked_actors)
        for actor in to_be_checked_actors:
            print(actor)
            db_actor = Actor.query.filter_by(
                first_name = actor["first_name"],
                last_name = actor["last_name"]
                ).first()
            print("ass")
            if db_actor is None:
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
            db_director = Director.query.filter_by(
                first_name = director["first_name"],
                last_name = director["last_name"]
                ).first()
            if db_director is None:
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
            db_streaming_service = StreamingService.query.filter_by(
                name = streaming_service["name"]
                ).first()
            if db_streaming_service is None:
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

        #db.session.add(movie)
        #db.session.commit()

        try:
            db.session.add(movie)
            db.session.commit()
        except IntegrityError as i_e:
            raise Conflict(description="Identical movie already exists.") from i_e
        return Response(status=201, headers={"Location": api.url_for(MovieItem, movie=movie)})

class ActorConverter(BaseConverter):
    '''Helper class to get Actor from url and url from actor'''
    def to_python(self, value):
        db_actor = Actor.query.filter_by(
            first_name = value.split(" ")[0],
            last_name = value.split(" ")[1]
            ).first()
        if db_actor is None:
            raise NotFound
        return db_actor

    def to_url(self, value):
        print(value)
        return value.first_name + " " + value.last_name
class ActorCollection(Resource):
    """Resource for getting all actors and adding new."""
    def post(self):
        """
        Add new actor to the database.
        ---
        description: Post new actor to the database
        requestBody:
            description: JSON formatted data
            content:
                application/JSON:
                    schema:
                        $ref: '#/components/schemas/Actor'
                    example:
                        fist_name: Scarlett
                        last_name: Johansson
        responses:
            '201':
                description: Actor added successfully
                headers:
                    Location:
                        description: URI of the actor added
                        schema:
                            type: string
            '409':
                description: Identical actor exists
        """

        first = str(request.json["first_name"])
        last = str(request.json["last_name"])
        actor = Actor(
            first_name=first, last_name=last
        )
        try:
            db.session.add(actor)
            db.session.commit()
        #TODO: doesn't work since our database model allows duplicate actors, , and  others
        except IntegrityError as i_e:
            raise Conflict(description="Identical actor already exists.") from i_e
        return Response(status=201, headers={"Location": api.url_for(ActorItem, actorname=actor)})

class ActorItem(Resource):
    """Resource for getting and modifying existing actor."""    
    def delete(self,actorname):
        """
        Method for deleting actor
        ---
        description: Delete actor by name
        parameters:
          - $ref: '#/components/parameters/actorname'
        responses:
            '204':
                description: Deleted actor successfully
            '404':
                description: Actor was not found
        """
        db.session.delete(actorname)
        db.session.commit()
        return Response(status=204)

    def get(self,actorname):
        """
        Get actor by name
        ---
        description: Get actor by name
        parameters:
          - $ref: '#/components/parameters/actorname'
        responses:
            '204':
                description: Got actor successfully
                content:
                    application/JSON:
                        schema:
                            $ref: '#/components/schemas/Actor'
                        example:
                            first_name: Emma
                            last_name: Watson
            '404':
                description: Actor was not found
        """
        print(actorname)
        return actorname.serialize()

    def put(self, actorname):
        #TODO TEST THIS METHOD

        """
        Edit existing actor
        ---
        description: Edit actor in the database
        parameters:
          - $ref: '#/components/parameters/actorname'
        requestBody:
            description: JSON formatted data
            content:
                application/JSON:
                    schema:
                        $ref: '#/components/schemas/Actor'
                    example:
                        fist_name: Scarlett
                        last_name: Johansson
        responses:
            '204':
                description: Actor modified successfully
                headers:
                    Location:
                        description: URI of the actor modified
                        schema:
                            type: string
            '409':
                description: Identical actor exists
            '404':
                description: Actor was not found
        """

        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Actor.json_schema())
        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e

        actorname.deserialize(request.json)

        try:
            db.session.add(actorname)
            db.session.commit()
        #TODO: doesn't work since our database model allows duplicate actors, , and  others
        except IntegrityError as i_e:
            raise Conflict(description="Identical actor already exists.") from i_e
        return Response(
            status=204,
            headers={"Location": api.url_for(ActorItem, actorname=actorname)}
            )
    
class StreamingConverter(BaseConverter):
    '''Helper class to get Streaming service from url and url from streaming service'''
    def to_python(self, value):
        db_ss = StreamingService.query.filter_by(name = value).first()
        if db_ss is None:
            raise NotFound
        return db_ss

    def to_url(self, value):
        print(value)
        return value.name

class StreamingCollection(Resource):
    """Resource for creating new streaming service."""
    def post(self):
        """
        Add new streaming service to the database. Does not permit adding movies to the service right now.
        ---
        description: Post new streaming service to the database
        requestBody:
            description: JSON formatted data
            content:
                application/JSON:
                    schema:
                        $ref: '#/components/schemas/StreamingService'
                    example:
                        name: Netflix
        responses:
            '201':
                description: StreamingService added successfully
                headers:
                    Location:
                        description: URI of the streaming service added
                        schema:
                            type: string
            '409':
                description: Identical streaming service exists
        """
        if not request.json:
            raise UnsupportedMediaType(415, "UnsupportedMediaType, JSON document required.")
        validator = Draft7Validator(
                StreamingService.json_schema(),
                format_checker=Draft7Validator.FORMAT_CHECKER
                )
        try:
            #print("Trying to validate request json")
            validator.validate(request.json)

        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e

        name = str(request.json["name"])
        streaming_service = StreamingService(
            name=name
        )
        try:
            db.session.add(streaming_service)
            db.session.commit()
        #TODO: doesn't work since our database model allows duplicate actors, , and  others
        except IntegrityError as i_e:
            raise Conflict(description="Identical streaming service already exists.") from i_e
        return Response(status=201, headers={"Location": api.url_for(StreamingItem, streamingservice=streaming_service)})
    
    
class StreamingItem(Resource):
    """Resource for getting and modifying existing streaming service."""
    def get(self, streamingservice):
        """
        Get a streaming service name and list of all titles in it.
        ---
        description: Get a streaming service name and list of all titles in it.
        parameters:
        - $ref: '#/components/parameters/streamingservice'
        responses:
            '200':
                description: Got movie details successfully
                content:
                    application/JSON:
                        schema:
                            $ref: '#/components/schemas/StreamingService'
                        example:
                            name: Netflix
                            movies:
                                - movie:
                                    title: Batman Begins
                                - movie:
                                    title: The Dark Knight
                                - movie:
                                    title: The Dark Knight Rises
            '404':
                description: Streaming service not found
        """
        print(streamingservice.name)
        return streamingservice.serialize()

    def put(self,streamingservice):
        #TODO: need to test/decide if we need to give all the movies when modifying the name.
        """
        Modify
        ---

        """
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, StreamingService.json_schema())
        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e
        streamingservice.deserialize(request.json)
        try:
            db.session.add(streamingservice)
            db.session.commit()
        #TODO: doesn't work since our database model allows duplicate actors, , and  others
        except IntegrityError as i_e:
            raise Conflict(description="Identical streaming service already exists.") from i_e
        return Response(status=204)

app.url_map.converters["movie"] = MovieConverter
app.url_map.converters["actorname"] = ActorConverter
app.url_map.converters["streamingservice"] = StreamingConverter
api.add_resource(MovieItem,"/movie/<movie:movie>/")
api.add_resource(MovieCollection,"/movie/")
api.add_resource(ActorCollection,"/actor/")
api.add_resource(ActorItem,"/actor/<actorname:actorname>/")
api.add_resource(StreamingCollection,"/streaming/")
api.add_resource(StreamingItem,"/streaming/<streamingservice:streamingservice>/")