"""
Campus Navigation System — Structured Logging
Formats application logs as single-line JSON records compatible with Google Cloud Logging.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from flask import g, request


class GoogleCloudJSONFormatter(logging.Formatter):
    """Formats log records as JSON objects for Cloud Logging."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Include request metadata if inside an active Flask request context
        try:
            if request:
                log_entry["httpRequest"] = {
                    "requestMethod": request.method,
                    "requestUrl": request.url,
                    "remoteIp": request.headers.get("X-Forwarded-For", request.remote_addr),
                    "userAgent": request.headers.get("User-Agent", ""),
                }
                if hasattr(g, "request_id"):
                    log_entry["requestId"] = g.request_id
        except RuntimeError:
            pass  # Outside request context

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(app):
    """Configure root and app loggers."""
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)

    if app.config.get("APP_ENV") == "production":
        handler.setFormatter(GoogleCloudJSONFormatter())
    else:
        # Clear readable formatting for local development
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
