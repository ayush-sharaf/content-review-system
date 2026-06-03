import ast
from datetime import datetime

COLLECTION = "movies"

# Holds precomputed lookups (e.g. the distinct language list) so read paths
# don't recompute them on every request.
FACETS_COLLECTION = "facets"

DATE_FORMAT = "%Y-%m-%d"


def parse_row(raw):
    """Turn a raw CSV row into a movie document, or None if it is unusable."""
    title = _clean(raw.get("title"))
    if not title:
        return None

    release_date = _parse_date(raw.get("release_date"))
    vote_average = _to_float(raw.get("vote_average"))
    vote_count = _to_int(raw.get("vote_count"))
    return {
        "title": title,
        "original_title": _clean(raw.get("original_title")),
        "overview": _clean(raw.get("overview")),
        "homepage": _clean(raw.get("homepage")),
        "status": _clean(raw.get("status")),
        "original_language": _clean(raw.get("original_language")).lower(),
        "languages": _parse_list(raw.get("languages")),
        "release_date": release_date,
        "year": release_date.year if release_date else None,
        "budget": _to_float(raw.get("budget")),
        "revenue": _to_float(raw.get("revenue")),
        "runtime": _to_int(raw.get("runtime")),
        "vote_average": vote_average,
        "vote_count": vote_count,
        "production_company_id": _to_int(raw.get("production_company_id")),
        "genre_id": _to_int(raw.get("genre_id")),
        # Precomputed at write time so sorts can push empty values last using
        # an index, instead of an in-memory sort on a computed field. A rating
        # only counts as real when the movie actually has votes: a 0.0 average
        # from 0 votes is "unrated", not a genuine low score.
        "has_release_date": release_date is not None,
        "has_rating": vote_average is not None and bool(vote_count),
    }


# Internal sort helpers that should not leak into API responses.
_INTERNAL_FIELDS = ("has_release_date", "has_rating")


def serialize(doc):
    """Make a stored document JSON friendly for API responses."""
    for field in _INTERNAL_FIELDS:
        doc.pop(field, None)
    doc["_id"] = str(doc["_id"])
    release_date = doc.get("release_date")
    if isinstance(release_date, datetime):
        doc["release_date"] = release_date.strftime(DATE_FORMAT)
    return doc


def _clean(value):
    return value.strip() if isinstance(value, str) else ""


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_date(value):
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT)
    except (AttributeError, ValueError):
        return None


def _parse_list(value):
    """The languages column holds a Python list literal, e.g. ['English']."""
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed]
    return []
