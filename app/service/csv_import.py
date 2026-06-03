import csv
import io

from app.models.movie import COLLECTION, FACETS_COLLECTION, parse_row


def import_csv(stream, database, batch_size):
    """Stream a CSV upload into MongoDB in batches.

    The file is read row by row so an upload of up to 1GB never has to be
    held in memory all at once.
    """
    # Lenient decoding: a stray bad byte in a large file is replaced rather
    # than aborting the whole import.
    reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8", errors="replace", newline=""))
    collection = database[COLLECTION]

    inserted = 0
    skipped = 0
    batch = []
    languages = set()
    try:
        for raw in reader:
            doc = parse_row(raw)
            if doc is None:
                skipped += 1
                continue
            languages.update(doc["languages"])
            batch.append(doc)
            if len(batch) >= batch_size:
                inserted += _flush(collection, batch)
                batch = []
    except csv.Error:
        # Structurally broken input (e.g. a binary file with NUL bytes).
        raise ValueError("The uploaded file is not a valid CSV")

    if batch:
        inserted += _flush(collection, batch)

    # Record the languages seen so the filter dropdown reads them in O(1)
    # instead of scanning the data on every request.
    _record_languages(database, languages)

    return {"inserted": inserted, "skipped": skipped}


def _flush(collection, batch):
    result = collection.insert_many(batch, ordered=False)
    return len(result.inserted_ids)


def _record_languages(database, languages):
    if not languages:
        return
    database[FACETS_COLLECTION].update_one(
        {"_id": "languages"},
        {"$addToSet": {"values": {"$each": sorted(languages)}}},
        upsert=True,
    )
