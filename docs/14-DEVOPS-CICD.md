# 14 — DevOps & CI/CD Pipeline Architecture

## 1. Automated Delivery Pipeline (Google Cloud Build)

```
 [Git Push: main / release]
              │
              ▼
   ┌───────────────────────┐
   │ Stage 1: Static Lint  │  ──► flake8, black, isort
   └──────────┬────────────┘
              │
              ▼
   ┌───────────────────────┐
   │ Stage 2: Unit & API   │  ──► pytest tests/ --cov=app --cov-report=xml
   │          Test Gates   │
   └──────────┬────────────┘
              │
              ▼
   ┌───────────────────────┐
   │ Stage 3: Docker Build │  ──► Multi-stage build (distroless/python-slim)
   │          & Security   │      Trivy container security scan
   └──────────┬────────────┘
              │
              ▼
   ┌───────────────────────┐
   │ Stage 4: Registry     │  ──► Push immutable tag to Artifact Registry
   └──────────┬────────────┘
              │
              ▼
   ┌───────────────────────┐
   │ Stage 5: Deploy Run   │  ──► gcloud run deploy campus-nav --image ...
   └──────────┬────────────┘
              │
              ▼
   ┌───────────────────────┐
   │ Stage 6: Smoke Tests  │  ──► Health check /ready and /health verification
   └───────────────────────┘
```

---

## 2. Docker Multi-Stage Containerization Architecture

The production `Dockerfile` enforces security best practices:
- Base image: `python:3.11-slim-bookworm` (small footprint, minimal CVE surface).
- Build tools isolated in builder stage to prevent compiling utilities leaking into runtime.
- Non-root user: `appuser:appgroup` (UID/GID 10001) execution.
- Gunicorn entrypoint with configurable workers, threads, and timeout.
- Explicit healthcheck instruction.

---

## 3. Rollback & Zero-Downtime Revisions
Google Cloud Run automatically manages immutable revisions:
- Each deployment creates a new versioned revision (e.g. `campus-nav-00042-xyz`).
- Traffic splitting allows canary testing (e.g. 10% traffic to new revision, 90% to stable).
- Instant instantaneous rollback via `gcloud run services update-traffic --to-revisions=STABLE_REV=100` if smoke tests fail.
