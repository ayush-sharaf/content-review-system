import csv
import io

from app.models.movie import COLLECTION, parse_row


def import_csv(stream, database, batch_size):
    """Stream a CSV upload into MongoDB in batches.

    The file is read row by row so an upload of up to 1GB never has to be
    held in memory all at once.
    """
    reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8", newline=""))
    collection = database[COLLECTION]

    inserted = 0
    skipped = 0
    batch = []
    for raw in reader:
        doc = parse_row(raw)
        if doc is None:
            skipped += 1
            continue
        batch.append(doc)
        if len(batch) >= batch_size:
            inserted += _flush(collection, batch)
            batch = []

    if batch:
        inserted += _flush(collection, batch)

    return {"inserted": inserted, "skipped": skipped}


def _flush(collection, batch):
    result = collection.insert_many(batch, ordered=False)
    return len(result.inserted_ids)
