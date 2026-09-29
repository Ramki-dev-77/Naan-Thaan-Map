"""
Campus Navigation System — Application Configuration
Supports Development, Testing, and Production environments.
Database-free: configuration powered by static JSON data files.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

DEFAULT_APP_ENV = "production" if os.getenv("VERCEL") == "1" else "development"


class Config:
    """Base Configuration."""
    APP_ENV = os.getenv("APP_ENV", DEFAULT_APP_ENV)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-campus-nav-2026")
    DEBUG = False
    TESTING = False

    # Static Data Directory
    DATA_DIR = BASE_DIR / "app" / "data"

    # Session & Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Overridden in Production
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

    # Rate Limiting
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_STRATEGY = "fixed-window"

    # External Maps API (Optional)
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    """Development Configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing Configuration."""
    TESTING = True
    DEBUG = True
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production Configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SECRET_KEY = os.getenv("SECRET_KEY")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    """Retrieve active configuration object based on APP_ENV."""
    env = os.getenv("APP_ENV", Config.APP_ENV).lower()
    return config_by_name.get(env, DevelopmentConfig)
