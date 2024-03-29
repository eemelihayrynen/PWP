'''
Main code for our Movie search API
Sources for code:
https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/
https://github.com/enkwolf/pwp-course-sensorhub-api-example
'''
import json
from flask import Flask, Response, request, url_for
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
from justwatch import JustWatch
from tmdbv3api import TMDb
import tmdbv3api

just_watch = JustWatch(country='FI')
tmdb = TMDb()
tmdb.api_key = 'ADD_KEY'
tmdb.language = 'en'
tmdb_movies = tmdbv3api.Movie()

#TODO: divide code to separate files
#TODO: delete operations should be defined also on database model level,
#  e.g. cascade, set null...

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///moviesearch.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SWAGGER"] = {
    "title": "Movie Search API",
    "openapi": "3.0.3",
    "uiversion": 3,
    "doc_dir": "./doc",
}

MASON = "application/vnd.mason+json"
LINK_RELATIONS_URL = "/moviemeta/link-relations#"

MOVIE_ITEM_URL = "/movie/"
ACTOR_ITEM_URL = "/actor/"
STREAMING_ITEM_URL = "/streaming/"

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
    release_year = db.Column(db.Integer, nullable=False)
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

        data = MovieMetaBuilder(
            title = self.title,
            rating = self.rating,
            writer = self.writer,
            release_year = self.release_year,
            genres = self.genres,
        )
        if short_form:
            short_data = MovieMetaBuilder(
                title = self.title
            )
            short_data.add_namespace("mumeta", LINK_RELATIONS_URL)
            short_data.add_control("self", href=api.url_for(MovieItem, movie=self))

            short_data.add_control_edit_movie(self)
            short_data.add_control_delete_movie(self)
            #short_data.add_control_movie_poster_url(self)
            return short_data

        data["actors"] = []
        for actor in self.actors:
            data["actors"].append(actor.serialize())
        data["directors"] = []
        for director in self.directors:
            data["directors"].append(director.serialize())
        data["streaming_services"] = []
        for streaming_service in self.streaming_services:
            data["streaming_services"].append(streaming_service.serialize(short_form=True))

        data.add_namespace("mumeta", LINK_RELATIONS_URL)
        data.add_control("self", href=api.url_for(MovieItem, movie=self))

        data.add_control_edit_movie(self)
        data.add_control_delete_movie(self)
        data.add_control_movie_poster_url(self)

        return data

    def deserialize(self, doc):
        '''De-serialize function for Movie resource'''
        #WIP: a way to desearialize actors, directors, streamingservices
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
    def json_schema(short_form=False):
        '''JSON schema function for Movie schema validation'''
        if short_form:
            schema = {
            "type": "object",
            "required": ["title"]
            }
            props = schema["properties"] = {}
            props["title"] = {
                "description": "Name of the movie",
                "type": "string"
            }
            return schema

        schema = {
            "type": "object",
            "required": ["title"]
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
    __table_args__ = (
        db.UniqueConstraint("first_name", "last_name"),
    )

    movies = db.relationship("Movie", secondary=MovieActorsAssociation, back_populates='actors')

    def serialize(self):
        '''Serialize function for Actor resource'''
        data = MovieMetaBuilder(
            first_name = self.first_name,
            last_name = self.last_name
        )
        data.add_control("profile", href=ACTOR_ITEM_URL)
        data.add_namespace("mumeta", LINK_RELATIONS_URL)
        data.add_control("self", href=api.url_for(ActorItem, actorname=self))
        data.add_control("collection", href=url_for("actor"))
        data.add_control_edit_actor(self)
        data.add_control_delete_actor(self)
        return data

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
    __table_args__ = (
        db.UniqueConstraint("first_name", "last_name"),
    )

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
    name = db.Column(db.String(256), nullable=False, unique=True)

    movies = db.relationship(
        "Movie",
        secondary=MovieStreamingServicesAssociation,
        back_populates='streaming_services'
        )

    def serialize(self, short_form=False):
        '''Serialize function for StreamingService resource'''
        data = MovieMetaBuilder(
            name = self.name,
            id = self.id
        )
        data.add_namespace("mumeta", LINK_RELATIONS_URL)
        data.add_control("self", href=api.url_for(StreamingItem, streamingservice=self))
        data.add_control_add_streamingservice()
        if short_form:
            return data
        data["movies"] = []
        data.add_control("profile", href=STREAMING_ITEM_URL)
        for movie in self.movies:
            data["movies"].append(movie.serialize(short_form=True))


        return data

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
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    
    Note that child classes should set the *DELETE_RELATION* to the application
    specific relation name from the application namespace. The IANA standard
    does not define a link relation for deleting something.

    Taken from the course material
    """

    DELETE_RELATION = ""

    def add_error(self, title, details):


        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, name_space, uri):


        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][name_space] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):


        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

    def add_control_post(self, ctrl_name, title, href, schema):


        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_put(self, title, href, schema):


        self.add_control(
            "edit",
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_delete(self, title, href):


        self.add_control(
            "mumeta:delete",
            href,
            method="DELETE",
            title=title,
        )

    def add_control_movie_poster(self, title, href):

        self.add_control(
            "mumeta:poster",
            href,
            method="GET",
            title=title
        )

class MovieMetaBuilder(MasonBuilder):
    '''Helper Class for hypermedia controls'''
    def add_control_movies_all(self):
        self.add_control(
            "mumeta:movies-all",
            url_for("movie"),
            title="All movies"
        )

    def add_control_actors_all(self):
        self.add_control(
            "mumeta:actors-all",
            url_for("actor"),
            title="All actors",
            isHrefTemplate=True,
        )
    def add_control_streamingservices_all(self):
        self.add_control(
            "mumeta:streaminservices-all",
            url_for("streaming"),
            title="All streamingservices",
            isHrefTemplate=True,
        )

    def add_control_add_movie(self):
        href = url_for("movie")
        title = "Add a new movie"

        self.add_control_post(
            "mumeta:add-movie",
            title,
            href,
            Movie.json_schema()
        )

    def add_control_add_actor(self):
        self.add_control_post(
            "mumeta:add-actor",
            "Add a new actor",
            url_for("actor"),
            Actor.json_schema()
        )

    def add_control_add_streamingservice(self):
        self.add_control_post(
            "mumeta:add-streamingservice",
            "Add a streamingservice",
            url_for("streaming"),
            StreamingService.json_schema()
        )

    def add_control_delete_movie(self, movie):
        self.add_control_delete(
            "Delete this movie",
            api.url_for(MovieItem, movie=movie),
        )

    def add_control_delete_actor(self, actor):
        self.add_control_delete(
            "Delete this actor",
            api.url_for(ActorItem, actorname=actor),
        )

    def add_control_edit_movie(self, movie):
        self.add_control_put(
            "Edit this movie",
            api.url_for(MovieItem, movie=movie),
            Movie.json_schema()
        )

    def add_control_edit_actor(self, actor):
        self.add_control_put(
            "Edit this artist",
            api.url_for(ActorItem, actorname=actor),
            Actor.json_schema()
        )

    def add_control_movie_poster_url(self, movie):

        self.add_control_movie_poster(
            "Get movie poster",
            get_movie_poster_path(movie.title)
        )

class MovieConverter(BaseConverter):
    '''Helper class to get Movie from url and url from Movie'''
    def to_python(self, value):
        db_movie = Movie.query.filter_by(title=value).first()
        if db_movie is None:
            raise NotFound
        return db_movie

    def to_url(self, value):
        return value.title

def get_movie_poster_path(title):
    '''Helper function to get movie poster from movie title using tmbd API search'''
    #print(title)
    if tmdb.api_key == "ADD_KEY":
        return "no-image.png"
    search = tmdb_movies.search(title)
    if search is None:
        return "no-image.png"
    try:
        path = "https://image.tmdb.org/t/p/w500" + search[0].poster_path
    except IndexError:
        path = "no-image.png"
    return path

def check_streaming(movie):
    """
    This function when called will check if the existing movie has the correct streaming data 
    """
    movie_dict={
        "hbm":"HBO Max",
        "hbo":"HBO Max",
        "dnp":"Disney Plus",
        "nfx":"Netflix",
        "yle":"Yle Areena",
        "rtu":"Ruutu",
        "prv":"Amazon Prime Video",
        "vip":"Viaplay"
    }
    results = just_watch.search_for_item(query=movie.title)
    j,ss1 = 0,""
    try:
        for j in range(len(results["items"][0]["offers"][j])*2):
            try:
                if results["items"][0]["offers"][j]["monetization_type"] == "flatrate" or results["items"][0]["offers"][j]["monetization_type"] == "free":
                    streamer = results["items"][0]["offers"][j]["package_short_name"]
                    if streamer in movie_dict:
                        ss1 = movie_dict[streamer]
            except IndexError:
                print("no work")
                break
        if StreamingService.query.filter_by(name = ss1).first() is None:
            movie.streaming_services.append(StreamingService(name=ss1))
            ss1= StreamingService.query.filter_by(name = ss1).first()
        else:
            ss1 = StreamingService.query.filter_by(name = ss1).first()
        movie.streaming_services.append(ss1)
        return ss1
    except:
        print("no work here either")

class MovieItem(Resource):
    """Resource for getting (searching) existing movie or modifying it."""
    @swag_from("doc/movie/items/get.yml")
    def get(self, movie):
        """
        Get a movie with title
        """
        check_streaming(movie)
        body = movie.serialize()
        response = Response(
            json.dumps(body),
            200,
            headers={'Access-Control-Allow-Origin': '*'},
            mimetype = MASON
            )
        return response

    @swag_from("doc/movie/items/delete.yml")
    def delete(self,movie):
        """
        Method for deleting a movie
        """

        db.session.delete(movie)
        db.session.commit()
        return Response(
            status=204,
            headers={'Access-Control-Allow-Origin': '*',
                     "Access-Control-Allow-Methods": "GET, PUT, POST, DELETE"}
        )

    @swag_from("doc/movie/items/put.yml")
    def put(self, movie):
        """
        Modify existing movie
        """
        #TODO TEST THIS METHOD
        try:
            #DOC:If the request content type is not ``application/json``, this
            # will raise a 400 Bad Request error.
            request.json
        except BadRequest as b_r:
            raise UnsupportedMediaType(
                description="UnsupportedMediaType, JSON document required."
                ) from b_r
        try:
            validate(request.json,Movie.json_schema())
        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e

        movie.title = str(request.json["title"])
        #movie.comments = str(request.json["comments"])
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
        return Response(
            status=201,
            headers={"Location": api.url_for(MovieItem, movie=movie),
                     'Access-Control-Allow-Origin': '*',
                     'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                     'Access-Control-Allow-Headers': 'Content-Type, Location',
                     'Access-Control-Expose-Headers': 'Location'}
        )

    def options(self, movie):
        '''Hack to evade CORS policy on preflight request when client is deployed locally.'''
        return Response(
            headers={"Access-Control-Allow-Methods": "GET, PUT, POST, DELETE",
                     'Access-Control-Allow-Origin': '*',
                     'Access-Control-Allow-Headers': '*'}
            )

class MovieCollection(Resource):
    """Resource for getting all movies or adding a new."""
    def get(self):
        """
        Get all movies from the database
        """
        movies = Movie.query.all()
        data = MovieMetaBuilder()
        data.add_namespace("mumeta", LINK_RELATIONS_URL)
        data.add_control("self", href=request.path)
        data.add_control_movies_all()
        data.add_control_add_movie()
        data["items"] = []
        for movie in movies:
            data["items"].append(movie.serialize(short_form=True))

        response = Response(
            json.dumps(data),
            200,
            headers={'Access-Control-Allow-Origin': '*'},
            mimetype=MASON
            )

        return response

    def post(self):
        """
        Method to post a new movie to the db.
        """
        try:
            #DOC:If the request content type is not ``application/json``, this
            # will raise a 400 Bad Request error.
            request.json
        except BadRequest as b_r:
            raise UnsupportedMediaType(
                description="UnsupportedMediaType, JSON document required."
                ) from b_r
        validator = Draft7Validator(
                Movie.json_schema(),
                format_checker=Draft7Validator.FORMAT_CHECKER
                )
        try:
            print("Trying to validate request json")
            validator.validate(request.json)
        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e

        title = str(request.json["title"])
        #comments = str(request.json["comments"])
        rating = float(request.json["rating"])
        writer = str(request.json["writer"])
        release_year = int(request.json["release_year"])
        genres = str(request.json["genres"])
        to_be_checked_actors = list(request.json["actors"])
        to_be_checked_directors = list(request.json["directors"])
        to_be_checked_streaming_services = list(request.json["streaming_services"])

        movie = Movie(
            title=title,
            #comments=comments,
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
        return Response(
            status = 201,
            headers={
                     'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                     'Access-Control-Allow-Origin': '*',
                     'Access-Control-Allow-Headers': 'Content-Type',
                     'Access-Control-Expose-Headers': 'Location',
                     "Location": api.url_for(MovieItem, movie=movie)}
        )

    def options(self):
        '''Hack to evade CORS policy on preflight request when client is deployed locally.'''
        return Response(
            headers={"Access-Control-Allow-Methods": "GET, PUT, POST, DELETE, OPTIONS",
                     'Access-Control-Allow-Origin': '*',
                     'Access-Control-Allow-Headers': '*'}
            )

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
        """
        try:
            #DOC:If the request content type is not ``application/json``, this
            # will raise a 400 Bad Request error.
            request.json
        except BadRequest as b_r:
            raise UnsupportedMediaType(
                description="UnsupportedMediaType, JSON document required."
                ) from b_r
        validator = Draft7Validator(
                Actor.json_schema(),
                format_checker=Draft7Validator.FORMAT_CHECKER
                )
        try:
            validator.validate(request.json)
        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e
        first = str(request.json["first_name"])
        last = str(request.json["last_name"])
        actor = Actor(
            first_name=first, last_name=last
        )
        try:
            db.session.add(actor)
            db.session.commit()
        except IntegrityError as i_e:
            raise Conflict(description="Identical actor already exists.") from i_e
        return Response(status=201, headers={"Location": api.url_for(ActorItem, actorname=actor)})

class ActorItem(Resource):
    """Resource for getting and modifying existing actor."""
    @swag_from("doc/actor/actorname/delete.yml")
    def delete(self,actorname):
        """
        Method for deleting actor
        """
        db.session.delete(actorname)
        db.session.commit()

        return Response(status=204)

    @swag_from("doc/actor/actorname/get.yml")
    def get(self,actorname):
        """
        Get actor by name
        """
        body = actorname.serialize()
        response = Response(
            json.dumps(body),
            200,
            headers={'Access-Control-Allow-Origin': '*'},
            mimetype = MASON
            )
        return response

    @swag_from("doc/actor/actorname/put.yml")
    def put(self, actorname):
        #TODO TEST THIS METHOD

        """
        Edit existing actor
        """
        try:
            #DOC:If the request content type is not ``application/json``, this
            # will raise a 400 Bad Request error.
            request.json
        except BadRequest as b_r:
            raise UnsupportedMediaType(
                description="UnsupportedMediaType, JSON document required."
                ) from b_r
        validator = Draft7Validator(
                Actor.json_schema(),
                format_checker=Draft7Validator.FORMAT_CHECKER
                )
        try:
            validator.validate(request.json)
        except ValidationError as v_e:
            raise BadRequest(description=str(v_e)) from v_e
        actorname.deserialize(request.json)
        try:
            db.session.add(actorname)
            db.session.commit()
        #TODO: test that this works
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
    """Resource for creating new streaming service or getting all"""
    @swag_from("doc/streaming/get.yml")
    def get(self):
        """
        Get all streaming services from database.
        """
        services = StreamingService.query.all()
        data = MovieMetaBuilder()
        data.add_namespace("mumeta", LINK_RELATIONS_URL)
        data.add_control("self", href=request.path)
        data.add_control_streamingservices_all()
        data.add_control_add_streamingservice()
        data["items"] = []
        for service in services:
            data["items"].append(service.serialize(short_form=True))
        #response = Response(json.dumps(data), 200, mimetype=MASON)
        response = Response(
            json.dumps(data),
            200,
            headers={'Access-Control-Allow-Origin': '*'},
            mimetype=MASON)
        return response

    @swag_from("doc/streaming/post.yml")
    def post(self):
        """
        Add new streaming service to the database.
        Does not permit adding movies to the service right now.
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
        except IntegrityError as i_e:
            raise Conflict(description="Identical streaming service already exists.") from i_e

        return Response(
            status=201,
            headers={"Location": api.url_for(StreamingCollection,
                                             streamingservicename=streaming_service)}
            )

class StreamingItem(Resource):
    """Resource for getting and modifying existing streaming service."""
    @swag_from("doc/streaming/streamingservice/get.yml")
    def get(self, streamingservice):
        """
        Get a streaming service name and list of all titles in it.
        """
        body = streamingservice.serialize()
        response = Response(
            json.dumps(body),
            200,
            headers={'Access-Control-Allow-Origin': '*'},
            mimetype=MASON
            )
        return response

    @swag_from("doc/streaming/streamingservice/put.yml")
    def put(self,streamingservice):
        #TODO: need to test/decide if we need to give all the movies when modifying the name.
        """
        Modify existing streaming service
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
        streamingservice.deserialize(request.json)
        try:
            db.session.add(streamingservice)
            db.session.commit()
        except IntegrityError as i_e:
            raise Conflict(description="Identical streaming service already exists.") from i_e
        return Response(status=204)

@app.route("/api/")
def index():
    '''Entypoint path for the API'''
    links = [{'rel': 'MovieItem',
              'href': "/movie/<movie:movie>/",
              'methods': ['GET', 'PUT', 'DELETE']},
             {'rel': 'MovieCollection', 'href': "/movie/", 'methods': ['GET', 'POST']},
             {'rel': 'ActorCollection', 'href': "/actor/", 'methods': ['POST']},
             {'rel': 'ActorItem',
              'href': "/actor/<actorname:actorname>/",
              'methods': ['GET', 'PUT', 'DELETE']},
             {'rel': 'StreamingCollection', 'href': "/streaming/", 'methods': ['GET', 'POST']},
             {'rel': 'StreamingItem',
              'href': "/streaming/<streamingservice:streamingservice>/",
              'methods': ['GET', 'PUT']}
              ]
    body = {}
    body["links"] = links
    response = Response(
        json.dumps(body),
        200,
        headers={'Access-Control-Allow-Origin': '*'},
        mimetype = MASON
        )
    return response

@app.route("/moviemeta/link-relations/")
def send_link_relations_html():
    '''Link relations of our moviemeta hypermedia controls'''
    return "here be link relations"

app.url_map.converters["movie"] = MovieConverter
app.url_map.converters["actorname"] = ActorConverter
app.url_map.converters["streamingservice"] = StreamingConverter
api.add_resource(MovieItem,"/movie/<movie:movie>/", endpoint = "movies")
api.add_resource(MovieCollection,"/movie/", endpoint = "movie")
api.add_resource(ActorCollection,"/actor/", endpoint = "actor")
api.add_resource(ActorItem,"/actor/<actorname:actorname>/", endpoint="actors")
api.add_resource(StreamingCollection,"/streaming/", endpoint = "streaming")
api.add_resource(
    StreamingItem,
    "/streaming/<streamingservice:streamingservice>/",
      endpoint = "streamings"
    )
