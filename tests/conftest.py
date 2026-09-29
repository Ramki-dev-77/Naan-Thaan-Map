"""
Campus Navigation System — Pytest Configuration and Test Fixtures
Database-free: tests run using the in-memory data store.
"""
import pytest
from app import create_app
from app.config import TestingConfig
from app.data_store import data_store


@pytest.fixture(scope="session")
def app():
    """Session-wide application instance for testing."""
    test_app = create_app(TestingConfig)
    
    with test_app.app_context():
        data_store.load()
        yield test_app


@pytest.fixture(scope="function")
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def app_ctx(app):
    """Application context for operations."""
    with app.app_context():
        data_store.reset()
        yield
