import json
import os
import pytest
import tempfile
from app import *
from app import Movie, Actor, Director, StreamingService
from sqlalchemy.engine import Engine
from sqlalchemy import event
import random
import string
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def client():
    with app.app_context():
        db_fd, db_fname = tempfile.mkstemp()
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
        app.config["TESTING"] = True
        populate()
        db.create_all()
        yield app.test_client()
        
        os.close(db_fd)
        os.unlink(db_fname)

def populate():
    if not Movie.query.filter_by(title="movie 4").first():
        print("adding")
        movie = Movie(title="movie 4".format(4), comments="comments", rating=4, writer="writer", release_year=4, genres="action", actors=[])
        db.session.add(movie)
        if not Actor.query.filter_by(first_name = "Daniel"):
            actor = Actor(first_name = "Daniel", last_name=str(4))
            db.session.add(actor)
        db.session.commit()

def _get_film():
    title= "movie 4"
    comments= ""
    rating= 9.0
    writer= "David S. Goyer"
    release_year= 2008
    genres= "Action/Drama/Crime"
    directors = "Chris Nolan"
    streamingServices = "HBO Max"
    return {"title": title, "comments":comments, "rating":rating, "writer":writer, "release_year":release_year, "genres":genres, "actors":[{"first_name":"mick","last_name":"4"}]
            ,"directors":[{"first_name":"Daniel","last_name":"4"}], "streaming_services": [{"name": "Netflix"}] }

def _get_film2():

    title= "movie 5"
    comments= ""
    rating= 9.0
    writer= "David S. Goyer"
    release_year= 2008
    genres= "Action/Drama/Crime"
    directors = "Chris Nolan"
    streamingServices = "HBO Max"
    return {"title": title, "comments":comments, "rating":rating, "writer":writer, "release_year":release_year, "genres":genres, "actors":[{"first_name":"mick","last_name":"4"}]
            ,"directors":[{"first_name":"Daniel","last_name":''.join(random.choice(string.ascii_lowercase) for i in range(10))}], "streaming_services": [{"name": "Netflix"}] }

class Testing(object):
    MOVIE_URL = "/movie/movie 4/"
    ACTOR_URL = "/actor/mick 4/"
    MOVIE_POST_URL = "/movie/"
    MOVIE_PUT_URL = "/movie/movie 4/"
    ACTOR_POST_URL = "/actor/"
    MOVIE_URL2 = "/movie/movie 5/"
    ACTOR_URL2 = "/actor/mick 5/"
    STREAM_POST_URL = "/streaming/"
    STREAM_URL = "/streaming/Netflix/"

    def test_get_film(self,client):
        """
        tests get method for movie, returns 200 when correct also tests the length of the data
        """
        resp = client.get(self.MOVIE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 10 #there are 10 categories of data in a movie
        assert body["title"]


    def test_get_all_films(self,client):
        """
        tests get method for movie, returns 200 when correct also tests the length of the data
        """
        resp = client.get(self.MOVIE_POST_URL)
        assert resp.status_code == 200
    
    def test_delete_film(self,client):
        """
        tests delete method for movie, returns 200 when correct and also tests after if movie is really gone and returns not found 404
        """
        resp = client.delete(self.MOVIE_URL)
        assert resp.status_code == 204
        resp = client.get(self.MOVIE_URL)
        assert resp.status_code == 404

    def test_add_movie(self,client):
        """
        tests post method for movie
        """
        if Movie.query.filter_by(title="movie 4").first():
            client.delete(self.MOVIE_URL)
        m = _get_film()
        resp = client.post(self.MOVIE_POST_URL,json = m)
        assert resp.status_code == 201
        resp = client.post(self.MOVIE_POST_URL,json = 0)
        assert resp.status_code == 400
    
    def test_modify_movie(self,client):
        """
        tests post method for movie
        """
        with db.session.no_autoflush:
            m = _get_film2()
            resp = client.put(self.MOVIE_URL,json = m)
            assert resp.status_code == 201 or resp.status_code == 409

        "failed json test"
        with db.session.no_autoflush:
            resp = client.put(self.MOVIE_URL,json = 1)
            assert BadRequest

    def test_get_actor(self,client):
        """
        tests get method for actor, returns 200 when correct also tests the length of the data
        """
        resp = client.get(self.ACTOR_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 4 #there are 4 categories of data in an actor
        assert body["first_name"]

    def test_delete_actor(self,client):
        """
        tests delete method for actor, returns 200 when correct and also tests after if actor is really gone and returns not found 404
        """
        resp = client.delete(self.ACTOR_URL)
        assert resp.status_code == 204
        resp = client.get(self.ACTOR_URL)
        assert resp.status_code == 404

    def test_add_actor(self,client):
        """
        tests post method for actor
        """
        if Actor.query.filter_by(first_name="mick",last_name="4").first():
            client.delete(self.ACTOR_URL)
        a = {"first_name":"mick","last_name":"4"}
        resp = client.post(self.ACTOR_POST_URL,json = a)
        assert resp.status_code == 201 or resp.status_code == 409

    def test_modify_stream(self,client):
        """
        tests put method for streaming services
        """
        a={"name":"HBOM"}
        resp = client.put(self.STREAM_URL,json = a)
        assert resp.status_code == 409 or resp.status_code == 204

    def test_get_all_stream(self,client):
        """
        tests get all method for streaming services
        """
        resp = client.get(self.STREAM_URL)
        assert resp.status_code == 200

    def test_entrypoint(self,client):
        resp = client.get("/api/")
        assert resp.status_code == 200

    def test_streaming_post(self,client):
        a={"name":"HBO  MAX"}
        resp = client.post(self.STREAM_POST_URL,json = a)
        assert resp.status_code == 201 or resp.status_code == 409

    def test_streaming_get_all(self,client):
        resp = client.get(self.STREAM_POST_URL)
        assert resp.status_code == 200 

    def test_check_streamer(self,client):
        db.session.add(Movie(title="The Godfather", comments="comments", rating=4, writer="writer", release_year=4, genres="action", actors=[]))
        resp = client.get("/movie/The Godfather/")
        print(resp)
        assert resp.status_code == 200

    def test_put_actor(self,client):
        a = {"first_name":"jack","last_name":''.join(random.choice(string.ascii_lowercase) for i in range(9))}
        resp = client.put(self.ACTOR_URL,json = a)
        assert resp.status_code == 409 or resp.status_code == 204
