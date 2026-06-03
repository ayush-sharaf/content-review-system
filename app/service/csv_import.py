import csv
import io

from app.models.movie import COLLECTION, parse_row


def import_csv(stream, database):
    """Read a movie CSV upload and store the parsed rows in MongoDB."""
    reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8", newline=""))
    collection = database[COLLECTION]

    docs = []
    skipped = 0
    for raw in reader:
        doc = parse_row(raw)
        if doc is None:
            skipped += 1
            continue
        docs.append(doc)

    if docs:
        collection.insert_many(docs)
    return {"inserted": len(docs), "skipped": skipped}
