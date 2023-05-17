from justwatch import JustWatch
import json
from app import db
from app import app
from app import Movie, Actor, Director, StreamingService
from sqlalchemy.exc import IntegrityError
ctx = app.app_context()
ctx.push()
db.create_all()

just_watch = JustWatch(country='FI')
f = open("imdb_data.json") #https://data.world/data-hut/imdb-top-250-movies/workspace/file?filename=imdb_data.json
data = json.load(f)
writers = ["Maria Fowler", "Kelly Hudson", "Kenneth Cox", "Sharon Smith", "James O'Brien", "Devin Saunders",
    "Shirley Robbins", "Mr. Charles Goodwin II", "Lauren Mora", "Jennifer Hayes", "Troy Williamson",
    "Travis Thomas", "Aaron Ferguson", "Sean Navarro", "Linda McDaniel", "Elizabeth Price", "Amanda Clark",
    "Abigail Garcia", "Todd Salas", "Kimberly Wood", "Jose Collins", "Tracey Davis", "Nathan Sanchez",
    "Elizabeth Spencer", "Ronald Davies", "Joseph Gibbs", "Michael Reynolds", "Larry May Jr.", "Sarah Mason",
    "Joanne Sanders", "Roberto Mitchell MD", "Melanie Norris", "Juan White", "Nancy Harris", "Mrs. Kelly Padilla",
    "James Howard", "Joel Rodriguez", "Ashley Webb", "Elizabeth Howard", "Brianna Meza", "Katherine Duran",
    "Stacey Rivera", "Erin Barnes", "Lisa Parks", "Nicole Moore", "Kyle Pena", "Rachel Wilson", "Andrea Jones",
    "David Benton", "Lisa Taylor", "Holly Lane", "Amber Simon", "Kenneth Jenkins", "Marilyn Moore MD",
    "Thomas Johnson", "Diana Daniels", "Diana Pena", "Ricardo White", "Gregory Tapia", "John Brown",
    "Michelle Hurst", "Mr. Edward Juarez", "Jill Williams", "Steven Nelson", "Jessica Rivera",
    "Douglas Washington", "Timothy Smith", "Peter Baker", "Raymond Knight", "Sarah Johnson",
    "Cindy Harris", "Pamela Brown", "Erica Johnson", "Nicholas Carlson", "April Gallagher",
    "Elizabeth Craig", "Micheal Bartlett", "Gregory Hobbs", "Mary Rojas", "Mary Robinson",
    "Deborah Madden", "Candice Duncan", "Garrett Miller", "Nicholas Chapman", "Courtney Harris",
    "Adrienne Bradley", "Pamela Murphy", "Shawn Barker", "Adam Davila", "Stephanie Yoder",
    "Frank Serrano", "Logan Rose", "Joshua Ramirez", "Adrian Wilson", "Andrew McDowell",
    "Belinda Pearson", "Katrina Rivera", "Shannon Thomas", "Jill Newman", "Dean Alexander",
    "William Anderson", "Kelly Nelson PhD", "Elizabeth Dennis", "Jennifer Johnson",
    "Trevor Harrington", "Miranda Neal", "Annette Butler", "Kathryn Martinez", "Dr. Michael Martin",
    "Dr. Carol Cervantes", "Robert Jennings", "Lauren Johnson", "Mark Campbell", "Nicholas Cooley",
    "Stephanie Johnson", "Ronald Gray", "Charles Andrews", "Kelly Moore", "Jared Lucero",
    "Stephanie West", "Michael Turner", "Michele Hughes DDS", "William Cox", "Christopher Gomez",
    "Sarah Green", "Kimberly Ray", "Gregory Cline", "Meredith Cox", "Tiffany Beck", "Michael Cantu",
    "Charles Garza", "Alexander Russell", "Tyler Kane", "Lindsay Mendoza", "John Morris",
    "Gary Braun", "Melissa Woods", "Annette Miles", "Sydney Smith", "James Dalton", "Bianca Pruitt",
    "Duane Fisher", "Jennifer McDowell", "Nicole Lowery", "Kathy Williams", "John Fisher",
    "Raymond Harper", "Tara Clark", "Anthony Lopez", "Juan McIntosh", "Kyle Jordan",
    "Laura Allen", "Hector Chavez", "Tracy Larson", "Sean Jackson", "Matthew Neal", "Sarah Young",
    "Jason Brown", "Eric McLaughlin", "Michael Rhodes", "Jon Williams", "Colleen Stewart",
    "Joseph Long", "Julie Brown", "Sarah Johnson", "Beth Winters", "Jacob Dennis", "Allison Brown",
    "Erin Taylor", "Kristin Wood", "Robert Morris", "Cynthia Aguirre", "Nathan Beasley",
    "Tina Morton", "Stanley Reyes", "Rachel King", "Robert Long", "Arthur Rose", "Shawn Smith",
    "Julie Hahn", "Stephanie Farmer", "David Morgan", "Patricia Campbell", "Vincent Coleman",
    "Jessica Bennett", "Julie Miranda", "Brandi Evans", "Mike Ho", "Jennifer Walters",
    "Jasmine Valencia", "Dennis Cunningham", "Daniel Larson", "Daniel Romero", "Nicole Vance",
    "David Cox", "Gregory Gordon", "Zachary Rodgers", "Maria Goodman", "David Day", "Amanda Carter",
    "Cynthia Nguyen", "Alyssa Davis", "Luke Singh", "Kevin Powell", "Stephanie Smith",
    "Frederick Rogers", "Emily Taylor", "Mark Gray", "David Gordon", "Kevin Graham",
    "Brenda Patterson", "Miranda Leonard", "Joseph Reynolds", "Michael Daugherty",
    "James Moss", "Andrew Smith", "Leah Jones", "Julie Long", "Kathryn Gibson", "David Johnson",
    "Jeremy Young", "Pamela Nicholson", "Robert Douglas", "Lauren Carter", "Ralph Williams",
    "Ethan Silva", "Zachary Johnson", "Benjamin Ramos", "Rhonda Cruz", "James Carroll",
    "Shari Melendez", "Cynthia Gonzalez", "Christopher Strickland", "Brent Hall", "Lauren Charles",
    "Danielle Cooper", "Ronnie Owens", "Jean Murray", "Heather Aguirre", "Angel Simmons",
    "Maureen Crane", "Brandy Bailey MD", "Stephanie Snyder", "Elizabeth Rivera", "Tracy Cooke",
    "Benjamin Robertson", "Dr. Miranda Wright", "Samantha Munoz", "Angela Brown", "Stephen Baker"
]
y=0	
for i in data["movies"]:
	results = just_watch.search_for_item(query=i["movie_name"])
	j,ss1 = 0,""
	try:
		for j in range(len(results["items"][0]["offers"][j])*2):
			try:
				if results["items"][0]["offers"][j]["monetization_type"] == "flatrate" or results["items"][0]["offers"][j]["monetization_type"] == "free":
					streamer = results["items"][0]["offers"][j]["package_short_name"]
					
					if streamer == "hbm" or streamer == "hbo":
						ss1 = StreamingService(name="HBO Max")

					elif streamer == "dnp":
						ss1 = StreamingService(name="Disney Plus")

					elif streamer == "nfx":
						ss1 = StreamingService(name="Netflix")

					elif streamer == "yle":
						ss1 = StreamingService(name="Yle Areena")

					elif streamer == "rtu":
						ss1 = StreamingService(name="Ruutu")

					elif streamer == "prv":
						ss1 = StreamingService(name="Amazon Prime Video")

					elif streamer == "vip":
						ss1 = StreamingService(name="Viaplay")

				if ss1 != "":
					break
			except IndexError:
				break
	except:
		continue
	
	writer = writers[y]
	actor1 = Actor(
		first_name=i["actors_list"][0].split(" ")[0],
		last_name=(str(i["actors_list"][0].split(" ")[1:])).replace("['","").replace("']","").replace("', '", " ").replace('["',"").replace('"]',"")
	)
	
	db_actor = Actor.query.filter_by(first_name = actor1.first_name, last_name = actor1.last_name).first()
	if db_actor is None:
		pass
	else:
		actor1 = db_actor

	actor2 = Actor(
		first_name=i["actors_list"][1].split(" ")[0],
		last_name=(str(i["actors_list"][1].split(" ")[1:]).replace("['","").replace("']","").replace("', '", " ").replace('["',"").replace('"]',""))
	)

	db_actor = Actor.query.filter_by(first_name = actor2.first_name, last_name = actor2.last_name).first()
	if db_actor is None:
		pass
	else:
		actor2 = db_actor
	dir1 = Director(
		first_name=i["director_name"].split(" ")[0],
		last_name=(str(i["director_name"].split(" ")[1:]).replace("['","").replace("']","").replace("', '", " ")).replace('["',"").replace('"]',"")
	)
	db_dir = Director.query.filter_by(first_name = dir1.first_name, last_name = dir1.last_name).first()
	if db_dir is None:
		pass
	else:
		dir1 = db_dir
	if ss1 == "":
		ss1 = StreamingService(name="not streaming without rent or buy")
	db_ss = StreamingService.query.filter_by(name = ss1.name).first()
	if db_ss is None:
		pass
	else:
		ss1 = db_ss
	movie = Movie(
		title=i["movie_name"],
		directors=[dir1],
		streaming_services=[ss1],
		actors=[actor1,actor2],
		writer = writer,
		rating=float(i["rating"]),
		release_year=i["movie_year"],
		genres=i["genre"][0]
	)
	db_movie = Movie.query.filter_by(title=movie.title, release_year=movie.release_year ).first()
	if db_movie is None:
		print("Adding new movie: " + movie.title)
		db.session.add(movie)
		db.session.commit()
	else:
		print("Already in database: " + movie.title)
	y=y+1

