"""
Campus Navigation System — Application Factory
Initializes extensions, loads static data store, registers blueprints, security middleware, and health probes.
Database-free: powered by static JSON files in app/data/.
"""
import time
import uuid
from flask import Flask, jsonify, request, g
from app.config import BASE_DIR, get_config
from app.extensions import limiter, csrf
from app.data_store import data_store
from app.utils.logging import setup_logging
from app.utils.errors import register_error_handlers
from app.utils.security import apply_security_headers


def create_app(config_class=None):
    """Application factory for Campus Navigation System."""
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "public" / "static"),
        static_url_path="/static",
    )

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    if app.config.get("APP_ENV") == "production" and not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set when APP_ENV=production.")

    # Configure structured logging
    setup_logging(app)

    # Initialize extensions
    limiter.init_app(app)
    csrf.init_app(app)

    # Initialize in-memory data store from static JSON files
    data_store.init_app(app)

    # Register error handlers
    register_error_handlers(app)

    # Middleware: Request Lifecycle & Tracing
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = request.headers.get("X-Request-Id", str(uuid.uuid4())[:8])

    @app.after_request
    def after_request(response):
        # Calculate latency
        if hasattr(g, "start_time"):
            duration = round((time.time() - g.start_time) * 1000, 2)
            response.headers["X-Response-Time"] = f"{duration}ms"
        
        response.headers["X-Request-Id"] = getattr(g, "request_id", "")
        # Apply defense-in-depth security headers
        return apply_security_headers(response)

    # Health & Readiness Probes
    @app.route("/health", methods=["GET"])
    def health_check():
        """Liveness probe: verifies process is alive and accepting connections."""
        return jsonify({
            "status": "ok",
            "environment": app.config.get("APP_ENV"),
            "service": "campus-navigation-system"
        }), 200

    @app.route("/ready", methods=["GET"])
    def readiness_check():
        """Readiness probe: verifies in-memory data store is loaded and ready."""
        try:
            if data_store.is_ready():
                return jsonify({
                    "status": "ready",
                    "data_source": "static_json",
                    "campuses_count": len(data_store._campuses)
                }), 200
            else:
                return jsonify({
                    "status": "not_ready",
                    "data_source": "static_json",
                    "error": "Data store is not initialized"
                }), 503
        except Exception as e:
            app.logger.error(f"Readiness probe failure: {str(e)}")
            return jsonify({
                "status": "not_ready",
                "data_source": "static_json",
                "error": str(e)
            }), 503

    # Register Blueprints
    from app.api.v1 import api_v1_bp
    # Exempt API v1 from browser CSRF tokens (APIs use JSON payload + rate limiting)
    csrf.exempt(api_v1_bp)
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    from app.views.main import main_bp
    app.register_blueprint(main_bp)

    from app.views.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Register CLI commands
    from app.commands.seed import register_commands
    register_commands(app)

    return app
