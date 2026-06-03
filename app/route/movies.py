from flask import Blueprint, request

from app.common.errors import ApiError
from app.common.responses import success
from app.db import get_db
from app.service.csv_import import import_csv

movies_bp = Blueprint("movies", __name__, url_prefix="/api/v1/movies")


@movies_bp.post("/upload")
def upload_movies():
    """Ingest a movie CSV file sent in the 'file' multipart field."""
    file = request.files.get("file")
    if file is None or not file.filename:
        raise ApiError("A CSV file is required in the 'file' field")
    if not file.filename.lower().endswith(".csv"):
        raise ApiError("Only .csv files are supported")

    result = import_csv(file.stream, get_db())
    return success(result, status=201)
