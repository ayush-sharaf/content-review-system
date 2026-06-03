from flask import jsonify


def success(data, status=200):
    """Wrap a successful payload in the standard response envelope."""
    return jsonify({"success": True, "data": data}), status
