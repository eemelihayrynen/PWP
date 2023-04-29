from app import db
from app import app
from app import Movie, Actor, Director, StreamingService
ctx = app.app_context()
ctx.push()
db.create_all()



actor1 = Actor(
	first_name="Tim",
	last_name="Robbins"
)

actor2 = Actor(
	first_name="Morgan",
	last_name="Freeman"
)

dir1 = Director(
	first_name="Frank",
	last_name="Darabont"
)

ss1 = StreamingService(name="Netflix")
ss2 = StreamingService(name="Disney+")

movie = Movie(
	title="The Shawshank Redemption",
	directors=[dir1],
	streaming_services=[ss1,ss2],
	actors=[actor1,actor2],
	rating=9.2,
	writer="Stepher King",
	release_year="1994",
	genres="Drama"
)


db.session.add(movie)
db.session.commit()

entry = Movie.query.first()
print(type(entry))
entry.title
entry.directors
entry.rating
entry.release_year