from flask import current_app
from pymongo import ASCENDING, DESCENDING, MongoClient

from app.models.movie import COLLECTION


def init_db(app):
    """Connect to MongoDB and make the database available on the app."""
    client = MongoClient(app.config["MONGO_URI"])
    database = client[app.config["MONGO_DB"]]
    app.config["DB_CLIENT"] = client
    app.config["DB"] = database
    ensure_indexes(database)


def get_db():
    """Return the database bound to the current application."""
    return current_app.config["DB"]


def ensure_indexes(database):
    """Create the indexes that back the list filters and sorts."""
    movies = database[COLLECTION]
    movies.create_index([("year", ASCENDING)])
    movies.create_index([("original_language", ASCENDING)])
    movies.create_index([("languages", ASCENDING)])
    movies.create_index([("release_date", ASCENDING)])
    movies.create_index([("vote_average", DESCENDING)])
