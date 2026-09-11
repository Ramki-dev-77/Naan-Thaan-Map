"""
Campus Navigation System — Security Utilities & Middleware
Implements password hashing, authentication decorators, and HTTP security headers.
"""
from functools import wraps
from flask import session, redirect, url_for, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """Hash password using Werkzeug's default modern hashing (pbkdf2:sha256/scrypt)."""
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify plain password against stored hash."""
    if not hashed:
        return False
    return check_password_hash(hashed, password)


def login_admin(user_dict):
    """Establish an admin session."""
    session["admin_id"] = user_dict["id"]
    session["admin_username"] = user_dict["username"]
    session["admin_role"] = user_dict["role"]
    session.permanent = True


def logout_admin():
    """Clear admin session."""
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    session.pop("admin_role", None)


def is_admin_authenticated() -> bool:
    """Check if current session has an authenticated admin."""
    return "admin_id" in session


def admin_required(f):
    """Decorator to enforce admin authentication on views and API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_authenticated():
            if request.path.startswith("/api/"):
                return jsonify({
                    "status": "error",
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Administrator authentication required.",
                    }
                }), 401
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def apply_security_headers(response):
    """Add defense-in-depth HTTP security headers to all responses."""
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Prevent framing / clickjacking
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    # Enable browser XSS filter
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy (allows Leaflet CDN and inline scripts for maps)
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; "
        "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self';"
    )
    response.headers["Content-Security-Policy"] = csp
    return response
