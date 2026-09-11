# ==============================================================================
# Campus Navigation System — Production Multi-Stage Dockerfile
# Optimized for Google Cloud Run (Stateless, Fast Cold Start, Non-Root)
# ==============================================================================

# Build Stage
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Stage
FROM python:3.11-slim-bookworm AS runner

WORKDIR /app

# Install runtime spatial & postgres libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy installed wheels from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=production
ENV PORT=8080

# Copy application source code
COPY --chown=appuser:appgroup . /app

USER appuser

EXPOSE 8080

# Healthcheck against liveness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Launch production Gunicorn WSGI server
CMD exec gunicorn --config gunicorn.conf.py run:app
