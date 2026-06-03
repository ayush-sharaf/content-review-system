from flask import request

from app.common.errors import ApiError

# Endpoints under this prefix require an allowed role.
PROTECTED_PREFIX = "/api/"
DEFAULT_ROLE = "default_role"


def register_auth(app, enforcer):
    """Guard the API with casbin, reading the caller role from a header."""

    @app.before_request
    def enforce_policy():
        if request.method == "OPTIONS" or not request.path.startswith(PROTECTED_PREFIX):
            return None
        role = request.headers.get("X-Role", DEFAULT_ROLE)
        if not enforcer.enforce(role, request.path, request.method):
            raise ApiError("Forbidden", 403)
        return None
