from unittest.mock import patch

import mongomock
import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    MONGO_DB = "content_review_test"
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


@pytest.fixture
def client():
    # mongomock gives each test a fresh in-memory database, so no running
    # MongoDB is needed to exercise the full request path.
    with patch("app.db.MongoClient", mongomock.MongoClient):
        app = create_app(TestConfig)
    return app.test_client()
