from dotenv import load_dotenv
from flask import Flask, jsonify

from app.config import Config
from app.db import init_db


def create_app(config=None):
    """Build and configure the Flask application."""
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config or Config)

    init_db(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
