# Movie Search API

This repository contains code and [documentation](https://github.com/eemelihayrynen/PWP/wiki) of our Movie Search API implementation for the PWP course.

The API is written in Python programming language and uses Flask as microframework to aid the web development.

Were a using SQLite as the database engine for the API and SQLAlchemy toolkit as ORM to simplify database management.

## Setting up the environment

We recommend using Python virtual environments to run the API code.

### To setup the environment:

1. Create the virtual environment using virtualenv
2. Activate the environment
3. Install the required Python modules from the requirements.txt file

        pip install -r requirements.txt

### Setup tmdb for fetching poster images

Our API allows searching corresponding movie posters from the TMBD's API.
Link to the poster image is given as a hypermedia control in movie item's get request.

In order to use the API, you must add your own API key to the server code:

    tmdb.api_key = 'ADD_KEY'

## Populating the database
The database can be populated using the script inside the database folder adds top 250 imdb movies. Example of moviesearch.db can be found under database/instance.

    python populate.py

The database can be manually populated with movies from database/movies_json_examples.json by manually taking the values and posting them with talented api tester.

The full population script from IMDB/Rottentomatoes is still WIP

## Running the API server

To start the server after population, simply run:

    flask run

## Using the API client

The client composes of static html files.
To use the client, open any of the html files in your web browser.

## Testing the API
Make sure to populate the database before testing.
To run the functional tests, run:

    pytest my_test.py
    
And for test coverage, run:
       
    pytest my_test.py --cov-report term-missing --cov=app
    
## API Documentation

The documentation page of the API can be access when the flask server is running from the following address:

    http://127.0.0.1:5000/apidocs/
