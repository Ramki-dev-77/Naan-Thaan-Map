"""
Campus Navigation System — Production Gunicorn Configuration
Optimized for Google Cloud Run containerized deployment.
"""
import os
import multiprocessing

# Port binding: Cloud Run sets the PORT environment variable (default 8080)
port = os.getenv("PORT", "8080")
bind = f"0.0.0.0:{port}"

# Concurrency tuning
# For Cloud Run, 2 to 4 workers per container with threads per worker handles high throughput
workers = int(os.getenv("WEB_CONCURRENCY", 2))
threads = int(os.getenv("GUNICORN_THREADS", 4))
worker_class = "gthread"

# Request timeouts
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))
keepalive = 5

# Logging: Stream to stdout/stderr for Google Cloud Logging ingestion
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# Support Google Cloud Run HTTPS proxy headers
forwarded_allow_ips = "*"
secure_scheme_headers = {
    "X-FORWARDED-PROTO": "https",
}
