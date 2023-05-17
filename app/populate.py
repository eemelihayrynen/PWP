from justwatch import JustWatch
import json
from app import db
from app import app
from app import Movie, Actor, Director, StreamingService
ctx = app.app_context()
ctx.push()
db.create_all()

just_watch = JustWatch(country='FI')
f = open("imdb_data.json") #https://data.world/data-hut/imdb-top-250-movies/workspace/file?filename=imdb_data.json
data = json.load(f)

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
	print(i["movie_name"])

	actor1 = Actor(
		first_name=i["actors_list"][0].split(" ")[0],
		last_name=str(i["actors_list"][0].split(" ")[1:])
	)

	actor2 = Actor(
		first_name=i["actors_list"][1].split(" ")[0],
		last_name=str(i["actors_list"][1].split(" ")[1:])
	)
	dir1 = Director(
		first_name=i["director_name"].split(" ")[0],
		last_name=str(i["director_name"].split(" ")[1:])
	)
	if ss1 == "":
		ss1 = StreamingService(name="not streaming without rent or buy")

	movie = Movie(
		title=i["movie_name"],
		directors=[dir1],
		streaming_services=[ss1],
		actors=[actor1,actor2],
		rating=float(i["rating"]),
		release_year=i["movie_year"],
		genres=i["genre"][0]
	)
	db.session.add(movie)
	db.session.commit()
