from flask import Blueprint, current_app, request

from app.common.errors import ApiError
from app.common.params import parse_list_params
from app.common.responses import success
from app.db import get_db
from app.service.csv_import import import_csv
from app.service.movies import list_languages, list_movies

movies_bp = Blueprint("movies", __name__, url_prefix="/api/v1/movies")


@movies_bp.post("/upload")
def upload_movies():
    """Ingest a movie CSV file sent in the 'file' multipart field."""
    file = request.files.get("file")
    if file is None or not file.filename:
        raise ApiError("A CSV file is required in the 'file' field")
    if not file.filename.lower().endswith(".csv"):
        raise ApiError("Only .csv files are supported")

    try:
        result = import_csv(file.stream, get_db(), current_app.config["UPLOAD_BATCH_SIZE"])
    except ValueError as error:
        raise ApiError(str(error))
    return success(result, status=201)


@movies_bp.get("/languages")
def list_languages_route():
    """Return the distinct languages in the data, for the filter dropdown."""
    return success(list_languages(get_db()))


@movies_bp.get("")
def list_movies_route():
    """List movies with pagination, filtering and sorting.

    When sorting, records with an empty sort field (for example a movie with no
    release date) are always returned last, in both ascending and descending
    order, so real values are never pushed off the front of the results.
    """
    params = parse_list_params(
        request.args,
        current_app.config["DEFAULT_PAGE_SIZE"],
        current_app.config["MAX_PAGE_SIZE"],
    )
    try:
        return success(list_movies(get_db(), **params))
    except ValueError:
        # Raised only when an `after` cursor cannot be decoded.
        raise ApiError("Invalid pagination cursor")
