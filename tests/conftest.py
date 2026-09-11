"""
Campus Navigation System — Pytest Configuration and Test Fixtures
"""
import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.commands.seed import create_demo_data


@pytest.fixture(scope="session")
def app():
    """Session-wide application instance for testing."""
    test_app = create_app(TestingConfig)
    
    with test_app.app_context():
        db.create_all()
        create_demo_data()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def app_ctx(app):
    """Application context for database operations."""
    with app.app_context():
        yield
