# 15 — Google Cloud Production Deployment Guide

## 1. Runtime Architecture
The Flask service is stateless and reads campus information from JSON files bundled under `app/data/`. It requires no database, database secret, VPC connector, persistent disk, or database sidecar. The existing Cloud Build pipeline builds the container and deploys it to Cloud Run.

`SECRET_KEY` should be supplied through Secret Manager for production sessions. No `DATABASE_URL` or database secret is used.

## 2. Deploy to Cloud Run
Build and publish the image using the repository's `cloudbuild.yaml`, then deploy the image:

```bash
gcloud run deploy campus-nav \
  --image=us-central1-docker.pkg.dev/${PROJECT_ID}/campus-nav-repo/campus-nav:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest" \
  --set-env-vars="APP_ENV=production,LOG_LEVEL=INFO" \
  --cpu=1 \
  --memory=1Gi \
  --max-instances=20 \
  --port=8080
```

Cloud Run instances load the bundled datasets at startup. Campus, building, facility, room, and routing changes must be committed to the JSON files and redeployed. Admin mutations made to a running instance exist only in that instance's memory and are not durable.
