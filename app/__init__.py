from dotenv import load_dotenv
from flask import Flask, jsonify

from app.casbin.enforcer import build_enforcer
from app.common.errors import register_error_handlers
from app.config import Config
from app.db import init_db
from app.middleware.auth import register_auth
from app.route import register_routes


def create_app(config=None):
    """Build and configure the Flask application."""
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config or Config)

    init_db(app)
    register_routes(app)
    register_error_handlers(app)
    register_auth(app, build_enforcer())

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
