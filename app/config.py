import os


class Config:
    """Application configuration sourced from the environment."""

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "content_review")
