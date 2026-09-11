"""
Campus Navigation System — Centralized Error Handling
Standardizes all JSON error responses and HTTP error status codes.
"""
from datetime import datetime, timezone
import uuid
from flask import jsonify, g, request


class AppError(Exception):
    """Custom Application Error with code and HTTP status code."""
    def __init__(self, message, code="APPLICATION_ERROR", status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        return {
            "status": "error",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": getattr(g, "request_id", str(uuid.uuid4())[:8]),
            },
        }


def make_error_response(message, code, status_code, details=None):
    """Helper to generate standardized JSON error responses."""
    payload = {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(g, "request_id", str(uuid.uuid4())[:8]),
        },
    }
    return jsonify(payload), status_code


def register_error_handlers(app):
    """Register application-wide error handlers on Flask app."""

    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(400)
    def handle_bad_request(err):
        return make_error_response(
            message=getattr(err, "description", "Bad Request"),
            code="BAD_REQUEST",
            status_code=400,
        )

    @app.errorhandler(401)
    def handle_unauthorized(err):
        return make_error_response(
            message="Authentication is required to access this resource.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    @app.errorhandler(403)
    def handle_forbidden(err):
        return make_error_response(
            message="You do not have permission to access this resource.",
            code="FORBIDDEN",
            status_code=403,
        )

    @app.errorhandler(404)
    def handle_not_found(err):
        # If request asks for HTML (e.g. browser navigation), allow fallback or render 404
        if request.path.startswith("/api/"):
            return make_error_response(
                message=getattr(err, "description", "The requested resource was not found."),
                code="NOT_FOUND",
                status_code=404,
            )
        return make_error_response(
            message="The requested page was not found.",
            code="PAGE_NOT_FOUND",
            status_code=404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return make_error_response(
            message=f"The method {request.method} is not allowed for this endpoint.",
            code="METHOD_NOT_ALLOWED",
            status_code=405,
        )

    @app.errorhandler(429)
    def handle_rate_limit(err):
        return make_error_response(
            message="Rate limit exceeded. Please slow down your requests.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )

    @app.errorhandler(500)
    def handle_internal_server_error(err):
        # Never expose internal stack traces in production
        return make_error_response(
            message="An internal server error occurred. Please try again later.",
            code="INTERNAL_SERVER_ERROR",
            status_code=500,
        )
