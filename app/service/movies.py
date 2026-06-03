import math
import re

from app.models.movie import COLLECTION, serialize

# Maps the public sort key to the underlying document field.
SORT_FIELDS = {"release_date": "release_date", "rating": "vote_average"}


def list_movies(database, *, page, page_size, year, language, sort_by, sort_order):
    """Return a paginated, filtered and sorted page of movies.

    Records whose sort field is empty (e.g. a movie with no release date) are
    always placed at the end, regardless of the sort direction.
    """
    query = _build_query(year, language)
    collection = database[COLLECTION]

    total = collection.count_documents(query)
    items = _fetch_page(collection, query, page, page_size, sort_by, sort_order)

    return {
        "items": items,
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


def _fetch_page(collection, query, page, page_size, sort_by, sort_order):
    skip = (page - 1) * page_size
    field = SORT_FIELDS.get(sort_by)
    if not field:
        cursor = collection.find(query).skip(skip).limit(page_size)
        return [serialize(doc) for doc in cursor]

    cursor = collection.aggregate(_sort_pipeline(query, field, sort_order, skip, page_size))
    return [serialize(doc) for doc in cursor]


def _sort_pipeline(query, field, sort_order, skip, page_size):
    direction = -1 if sort_order == "desc" else 1
    return [
        {"$match": query},
        # Flag empty sort values so they always rank last, whatever the direction.
        {"$addFields": {"_missing": {"$cond": [{"$eq": [f"${field}", None]}, 1, 0]}}},
        {"$sort": {"_missing": 1, field: direction, "_id": 1}},
        {"$skip": skip},
        {"$limit": page_size},
        {"$project": {"_missing": 0}},
    ]
