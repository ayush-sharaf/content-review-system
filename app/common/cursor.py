import base64
import json
from datetime import datetime

from bson import ObjectId

DATE_FORMAT = "%Y-%m-%d"


def encode_cursor(doc, sort_keys):
    """Encode a document's sort-key values into an opaque cursor token."""
    values = [_encode_value(doc.get(field)) for field, _ in sort_keys]
    raw = json.dumps(values, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_cursor(token, sort_keys):
    """Decode a cursor token back into sort-key values. Raises ValueError if bad."""
    raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
    values = json.loads(raw)
    if not isinstance(values, list) or len(values) != len(sort_keys):
        raise ValueError("cursor does not match the current sort")
    return [_decode_value(item) for item in values]


def _encode_value(value):
    # bool must come before the generic case: bool is a subclass of int.
    if isinstance(value, bool):
        return {"t": "bool", "v": value}
    if isinstance(value, datetime):
        return {"t": "date", "v": value.strftime(DATE_FORMAT)}
    if isinstance(value, ObjectId):
        return {"t": "oid", "v": str(value)}
    return {"t": "raw", "v": value}


def _decode_value(item):
    kind = item["t"]
    if kind == "date":
        return datetime.strptime(item["v"], DATE_FORMAT)
    if kind == "oid":
        return ObjectId(item["v"])
    return item["v"]
