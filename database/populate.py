from app import db
from app import app
from app import Movie, Actor, Director, StreamingService

ctx = app.app_context()
ctx.push()

movie = Movie(id=1, title="The Shawshank Redemption", comments="NULL", rating=9.2, writer="Stepher King", release_year="1994", genres="Drama")

db.session.add(movie)
db.session.commit()

actor1 = Actor(id=1, first_name="Tim", last_name="Robbins", movie_id=1)
actor2 = Actor(id=2, first_name="Morgan", last_name="Freeman", movie_id=1)

db.session.add(actor1)
db.session.add(actor2)
db.session.commit()

dir1 = Director(id=1, first_name="Frank", last_name="Darabont", movie_id=1)

db.session.add(dir1)
db.session.commit()

ss1 = StreamingService(id=1, name="Netflix", movie_id=1)
ss2 = StreamingService(id=2, name="Disney+", movie_id=1)

db.session.add(ss1)
db.session.add(ss2)
db.session.commit()

ctx.pop()