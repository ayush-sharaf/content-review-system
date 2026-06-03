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

    # Filters.
    movies.create_index([("year", ASCENDING)])
    movies.create_index([("original_language", ASCENDING)])
    movies.create_index([("languages", ASCENDING)])

    # Sorts. The null flag keeps empty values last; _id gives a stable order
    # and powers keyset pagination. One index per direction so both the
    # ascending and descending sorts stay index-backed (no in-memory sort).
    movies.create_index([("has_release_date", DESCENDING), ("release_date", ASCENDING), ("_id", ASCENDING)])
    movies.create_index([("has_release_date", DESCENDING), ("release_date", DESCENDING), ("_id", DESCENDING)])
    movies.create_index([("has_rating", DESCENDING), ("vote_average", ASCENDING), ("_id", ASCENDING)])
    movies.create_index([("has_rating", DESCENDING), ("vote_average", DESCENDING), ("_id", DESCENDING)])
