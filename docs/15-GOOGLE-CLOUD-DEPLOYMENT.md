# 15 — Google Cloud Production Deployment Guide

## 1. Google Cloud Architecture Components
- **Compute**: Google Cloud Run (Fully managed, stateless, autoscaling 0 to 100 instances).
- **Database**: Cloud SQL for PostgreSQL 15 with PostGIS 3.3 extension enabled.
- **Secrets Management**: Google Secret Manager (`SECRET_KEY`, `DATABASE_URL`, `ADMIN_PASSWORD`).
- **VPC & Networking**: Serverless VPC Access Connector connecting Cloud Run to Cloud SQL private IP.
- **Container Registry**: Google Artifact Registry (`pkg.dev/${PROJECT_ID}/campus-nav-repo/campus-nav`).
- **CDN & Edge**: Google Cloud CDN and Cloud Armor for DDoS mitigation and SSL termination.

---

## 2. Infrastructure Setup Commands (CLI / IaC)

### Step 1: Enable Cloud APIs
```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  vpcaccess.googleapis.com
```

### Step 2: Create Artifact Registry Repository
```bash
gcloud artifacts repositories create campus-nav-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Campus Navigation Docker Repository"
```

### Step 3: Provision Cloud SQL (PostgreSQL with PostGIS)
```bash
gcloud sql instances create campus-nav-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-7680 \
  --region=us-central1 \
  --storage-auto-increase \
  --backup-start-time=02:00

# Create Database and PostGIS Extension
gcloud sql databases create campus_db --instance=campus-nav-db
gcloud sql users set-password postgres --instance=campus-nav-db --password="<STRONG_DB_PASSWORD>"
```

### Step 4: Configure Secrets in Secret Manager
```bash
echo -n "postgresql://postgres:<STRONG_DB_PASSWORD>@/<DB_NAME>?host=/cloudsql/<PROJECT_ID>:us-central1:campus-nav-db" | \
  gcloud secrets create DATABASE_URL --data-file=-

openssl rand -hex 32 | \
  gcloud secrets create SECRET_KEY --data-file=-
```

### Step 5: Deploy Cloud Run Service
```bash
gcloud run deploy campus-nav \
  --image=us-central1-docker.pkg.dev/${PROJECT_ID}/campus-nav-repo/campus-nav:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest" \
  --set-env-vars="APP_ENV=production,LOG_LEVEL=INFO" \
  --add-cloudsql-instances=${PROJECT_ID}:us-central1:campus-nav-db \
  --cpu=1 \
  --memory=1Gi \
  --min-instances=1 \
  --max-instances=20 \
  --port=8080
```
