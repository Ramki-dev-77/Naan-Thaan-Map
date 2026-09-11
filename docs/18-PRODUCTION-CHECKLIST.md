# 18 — Production Readiness & Pre-Flight Checklist

Before approving release to production traffic, verify every item below:

## 1. Security & Credentials
- [ ] No hardcoded passwords, API secrets, or private keys committed to Git repository.
- [ ] `SECRET_KEY` generated using 256-bit cryptographically secure entropy (`openssl rand -hex 32`) and loaded via Secret Manager.
- [ ] Database credentials loaded securely from Google Secret Manager via IAM permissions.
- [ ] Flask debug mode strictly disabled (`FLASK_DEBUG=0`, `APP_ENV=production`).
- [ ] Cookie flags verified: `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE=Lax`.
- [ ] CSRF protection enabled and active on all state-altering endpoints.
- [ ] Rate limiting (Flask-Limiter) active on `/api/v1/search`, `/api/v1/routes`, and `/api/v1/admin/login`.

## 2. Infrastructure & Networking
- [ ] Google Cloud Run service configured with Serverless VPC Connector to private Cloud SQL instance.
- [ ] PostgreSQL PostGIS extension enabled (`CREATE EXTENSION IF NOT EXISTS postgis;`).
- [ ] GIST spatial indexes built on all geometry columns (`boundary`, `footprint`, `location`).
- [ ] Container configured to run as non-root unprivileged user (`UID 10001`).
- [ ] Gunicorn WSGI server running with at least 2 workers per core and asynchronous/sync worker tuning.
- [ ] Readiness probe (`/ready`) and Liveness probe (`/health`) configured in Cloud Run service spec.

## 3. Map & Routing Integrity
- [ ] Sample seed campus data verified for physical graph connectivity (no partitioned components).
- [ ] Geolocation accuracy threshold badges verified on mobile devices.
- [ ] GPS degradation banner displays correctly when accuracy > 50m or when indoors.
- [ ] Accessible route toggle strictly bypasses all staircases.
- [ ] Manual origin selection fallback functions seamlessly without location permissions.

## 4. Observability & Backups
- [ ] Cloud SQL automated daily backups enabled with 7-day point-in-time recovery.
- [ ] Structured JSON logging emitting severity and request metadata to Cloud Logging.
- [ ] Cloud Monitoring alert policies configured for 5xx error spikes (>2%) and P95 latency (>500ms).
