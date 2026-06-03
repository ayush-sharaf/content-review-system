import math

from app.common.cursor import decode_cursor, encode_cursor
from app.models.movie import COLLECTION, serialize

# Maps the public sort key to the document field and its precomputed null flag.
SORT_FIELDS = {
    "release_date": {"field": "release_date", "flag": "has_release_date"},
    "rating": {"field": "vote_average", "flag": "has_rating"},
}


def list_languages(database):
    """Distinct languages present in the data, sorted for filter dropdowns."""
    values = database[COLLECTION].distinct("languages")
    return sorted(value for value in values if value)


def list_movies(database, *, page, page_size, year, languages, sort_by, sort_order, after=None):
    """Return a page of movies, filtered and sorted.

    Two pagination modes share the same sort:
      - offset (default): page/page_size with a total count, good for shallow
        page jumps in the CRM.
      - keyset (when a cursor is supplied): seeks past the last seen record,
        staying fast no matter how deep the traversal goes.

    Records whose sort field is empty are always placed last, in either
    direction, backed by an index on the precomputed null flag.
    """
    collection = database[COLLECTION]
    base_query = _build_query(year, languages)
    sort_keys = _sort_keys(sort_by, sort_order)

    if after is not None:
        cursor_values = decode_cursor(after, sort_keys)
        return _keyset_page(collection, base_query, sort_keys, page_size, cursor_values)
    return _offset_page(collection, base_query, sort_keys, page, page_size)


def _offset_page(collection, base_query, sort_keys, page, page_size):
    skip = (page - 1) * page_size
    docs = list(collection.find(base_query).sort(sort_keys).skip(skip).limit(page_size))
    total = collection.count_documents(base_query)
    next_cursor = _next_cursor(docs, sort_keys, page_size)
    return {
        "items": [serialize(doc) for doc in docs],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size),
        "next_cursor": next_cursor,
        "has_more": skip + len(docs) < total,
    }


def _keyset_page(collection, base_query, sort_keys, page_size, cursor_values):
    query = _keyset_query(base_query, sort_keys, cursor_values)
    docs = list(collection.find(query).sort(sort_keys).limit(page_size))
    next_cursor = _next_cursor(docs, sort_keys, page_size)
    return {
        "items": [serialize(doc) for doc in docs],
        "page_size": page_size,
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None,
    }


def _build_query(year, languages):
    query = {}
    if year is not None:
        query["year"] = year
    if languages:
        # AND semantics: a movie must list every selected language. The values
        # come from the dataset's own language list, so an exact match is used.
        query["languages"] = {"$all": languages}
    return query


def _sort_keys(sort_by, sort_order):
    """Build the compound sort. The null flag (descending) keeps empty values
    last; the field and _id give a stable, index-backed total order."""
    spec = SORT_FIELDS.get(sort_by)
    if not spec:
        return [("_id", 1)]
    direction = -1 if sort_order == "desc" else 1
    return [(spec["flag"], -1), (spec["field"], direction), ("_id", direction)]


def _keyset_query(base_query, sort_keys, values):
    """Seek to the records that come after the cursor, honouring every sort key.

    For keys k0..kn the boundary is the usual lexicographic comparison:
    (k0 after) OR (k0 equal AND k1 after) OR ...
    """
    or_clauses = []
    for i, (field, direction) in enumerate(sort_keys):
        clause = {sort_keys[j][0]: values[j] for j in range(i)}
        clause[field] = {"$gt" if direction == 1 else "$lt": values[i]}
        or_clauses.append(clause)

    boundary = {"$or": or_clauses}
    return {"$and": [base_query, boundary]} if base_query else boundary


def _next_cursor(docs, sort_keys, page_size):
    if not docs or len(docs) < page_size:
        return None
    return encode_cursor(docs[-1], sort_keys)
