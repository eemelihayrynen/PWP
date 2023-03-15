import json
from flask import Flask, Response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_restful import Api, Resource
#from marshmallow import Schema, fields

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
        title = str(request.json["title"])
        comments = str(request.json["comments"])
        rating = float(request.json["rating"])
        writer = str(request.json["writer"])
        release_year = int(request.json["release_year"])
        genres = str(request.json["genres"])
        actors = list(request.json["actors"]) 

        movie = Movie(
            title=title, comments=comments, rating=rating, writer=writer, release_year=release_year, genres=genres
        )
        print(actors)
        for actor in actors:
            print(actor)
            db_actor = Actor.query.filter_by(first_name = actor.split(" ")[0],last_name = actor.split(" ")[1]).first()
            if db_actor == None:
                return "Actor not found"
                
            
        db.session.add(movie)
        db.session.commit()
        for actor in actors:
            db_actor = Actor.query.filter_by(first_name = actor.split(" ")[0],last_name = actor.split(" ")[1]).first()

            movie.actors.append(db_actor)
            db.session.commit()
            print(db_actor.id)
        resp =Response()
        resp.status=201
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

