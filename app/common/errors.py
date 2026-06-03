from flask import jsonify


class ApiError(Exception):
    """An error that maps directly to an HTTP status and client message."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({"success": False, "error": error.message}), error.status

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"success": False, "error": "Not found"}), 404

    @app.errorhandler(500)
    def handle_server_error(_error):
        return jsonify({"success": False, "error": "Internal server error"}), 500
