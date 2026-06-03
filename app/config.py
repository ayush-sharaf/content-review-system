import os


class Config:
    """Application configuration sourced from the environment."""

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "content_review")

    # Rows are inserted in batches so a 1GB upload never sits fully in memory.
    UPLOAD_BATCH_SIZE = int(os.getenv("UPLOAD_BATCH_SIZE", "5000"))

    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
