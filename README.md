# Campus Navigation System

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/framework-Flask_3.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Leaflet](https://img.shields.io/badge/maps-Leaflet_1.9-green.svg)](https://leafletjs.com/)
[![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL_%2B_PostGIS-blue.svg)](https://postgis.net/)
[![Cloud Run](https://img.shields.io/badge/deployment-Google_Cloud_Run-blue.svg)](https://cloud.google.com/run)

A production-ready, multi-campus, interactive campus navigation platform designed to provide students, visitors, and faculty with real-time pedestrian routing, multi-attribute location search, honest location accuracy modeling, and administrative topology management.

---

## Key Features

1. **Interactive Vector Campus Map**:
   - High-fidelity campus boundary polygons, building footprints, entrances, and categorized facility points of interest rendered via Leaflet.
2. **Campus Pedestrian Graph & A* Routing**:
   - Self-contained, zero-API-cost routing engine calculating true pedestrian pathways, distances, and walking times.
   - Wheelchair and stroller accessibility routing (`accessible=true`) strictly avoiding staircases.
3. **Multi-Attribute Search**:
   - Instant search across building codes, room numbers, academic departments, laboratories, and outdoor facilities with tiered prefix/fuzzy ranking.
4. **Honest Geolocation & Privacy by Design**:
   - Standard W3C Geolocation with live accuracy radius indicator (`±X m`).
   - Categorized UX states (Excellent, Good, Usable, Approximate, Poor) with anti-jitter smoothing.
   - Clear indoor signal attenuation warnings and automatic fallback to manual origin selection.
   - Zero storage of raw user telemetry.
5. **Role-Based Administration**:
   - CSRF-protected admin console for managing campuses, buildings, rooms, facilities, and the walkable graph network with immutable audit logs.
6. **Cloud-Native Deployment**:
   - Ready for Google Cloud Run, Cloud SQL (PostGIS), Secret Manager, and Google Cloud Build CI/CD.

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- PostgreSQL 15+ with PostGIS extension (or local test runner)

### 2. Environment Setup
```bash
# Clone and enter directory
cd Cloud_mini

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### 3. Initialize Database & Seed Demo Data
```bash
# Initialize database tables and seed realistic demo campus
flask seed-demo
```

### 4. Run Application
```bash
# Start development server
python run.py
```
Navigate to `http://localhost:5000` in your web browser.

---

## Architectural Documentation

The project includes an exhaustive enterprise documentation suite in the `docs/` directory:
- [00 — Master Prompt](docs/00-MASTER-PROMPT.md)
- [01 — Product Requirements Document](docs/01-PRODUCT-REQUIREMENTS.md)
- [02 — Functional Requirements](docs/02-FUNCTIONAL-REQUIREMENTS.md)
- [03 — Non-Functional Requirements](docs/03-NON-FUNCTIONAL-REQUIREMENTS.md)
- [04 — Tech Stack & Rationale](docs/04-TECH-STACK.md)
- [05 — System Architecture](docs/05-SYSTEM-ARCHITECTURE.md)
- [06 — Database Design & Spatial Schema](docs/06-DATABASE-DESIGN.md)
- [07 — REST API Specification](docs/07-API-SPECIFICATION.md)
- [08 — Location & GPS Architecture](docs/08-LOCATION-AND-GPS-ARCHITECTURE.md)
- [09 — Map & Routing Engine Architecture](docs/09-MAP-AND-ROUTING-ARCHITECTURE.md)
- [10 — Frontend Architecture](docs/10-FRONTEND-ARCHITECTURE.md)
- [11 — Backend Architecture](docs/11-BACKEND-ARCHITECTURE.md)
- [12 — Security & Compliance](docs/12-SECURITY-REQUIREMENTS.md)
- [13 — Testing Strategy](docs/13-TESTING-STRATEGY.md)
- [14 — DevOps & CI/CD Pipeline](docs/14-DEVOPS-CICD.md)
- [15 — Google Cloud Deployment Guide](docs/15-GOOGLE-CLOUD-DEPLOYMENT.md)
- [16 — Monitoring, Observability & Health](docs/16-MONITORING-AND-OBSERVABILITY.md)
- [17 — Data Import & Admin Guide](docs/17-DATA-IMPORT-AND-ADMIN-GUIDE.md)
- [18 — Production Readiness Checklist](docs/18-PRODUCTION-CHECKLIST.md)
- [19 — Future Roadmap](docs/19-FUTURE-ROADMAP.md)

---

## Running Tests

Execute the automated test suite with coverage:
```bash
pytest tests/ -v
```

---

## License
Proprietary — Campus Navigation System Architecture. All Rights Reserved.
