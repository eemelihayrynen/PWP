import yaml
from app import Movie, Actor, Director, StreamingService

print(yaml.dump(Movie.json_schema()))

print(yaml.dump(Actor.json_schema()))

print(yaml.dump(Director.json_schema()))

print(yaml.dump(StreamingService.json_schema()))