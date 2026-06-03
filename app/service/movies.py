import math
import re

from pymongo import ASCENDING, DESCENDING

from app.models.movie import COLLECTION, serialize

# Maps the public sort key to the underlying document field.
SORT_FIELDS = {"release_date": "release_date", "rating": "vote_average"}


def list_movies(database, *, page, page_size, year, language, sort_by, sort_order):
    """Return a paginated, filtered and sorted page of movies."""
    query = _build_query(year, language)
    collection = database[COLLECTION]

    total = collection.count_documents(query)
    cursor = collection.find(query)
    sort = _build_sort(sort_by, sort_order)
    if sort:
        cursor = cursor.sort(sort)
    cursor = cursor.skip((page - 1) * page_size).limit(page_size)

    return {
        "items": [serialize(doc) for doc in cursor],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size),
    }


def _build_query(year, language):
    query = {}
    if year is not None:
        query["year"] = year
    if language:
        # Match either the language code (original_language) or a readable
        # name in the languages list, both case-insensitively.
        pattern = re.compile(f"^{re.escape(language)}$", re.IGNORECASE)
        query["$or"] = [{"original_language": pattern}, {"languages": pattern}]
    return query


def _build_sort(sort_by, sort_order):
    field = SORT_FIELDS.get(sort_by)
    if not field:
        return None
    direction = DESCENDING if sort_order == "desc" else ASCENDING
    return [(field, direction)]
