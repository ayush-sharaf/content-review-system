from dotenv import load_dotenv
from flask import Flask, jsonify


def create_app():
    """Build and configure the Flask application."""
    load_dotenv()
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
