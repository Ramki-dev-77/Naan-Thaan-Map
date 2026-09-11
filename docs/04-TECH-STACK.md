# 04 — Technology Stack & Decision Rationale

## 1. Stack Overview

| Layer | Selected Technology | Version / Specification | Rationale & Alternatives Considered |
|---|---|---|---|
| **Runtime & Language** | Python | 3.10+ (Target 3.12) | Rich GIS ecosystem, high developer velocity, mature enterprise libraries. |
| **Web Framework** | Flask | 3.0+ | Lightweight, un-opinionated, zero bloat, rapid cold start on Cloud Run compared to Django. |
| **WSGI Server** | Gunicorn | 22.0+ | Battle-tested production WSGI HTTP server with worker-timeout and concurrency controls. |
| **ORM & Spatial** | SQLAlchemy + GeoAlchemy2 | 2.0+ / 0.14+ | Standard Python ORM with spatial type definitions (Geometry, Point, Polygon, LineString). |
| **Database Engine** | PostgreSQL + PostGIS | 15+ / 3.3+ | Industry standard relational geospatial database with spatial indexes (GIST) and ST_* functions. |
| **Database Migrations** | Alembic / Flask-Migrate | 4.0+ | Schema version control, repeatable automated deployments. |
| **Frontend Mapping** | Leaflet | 1.9.4 | Open-source, vendor-agnostic, lightweight (38 KB gzipped), highly extensible via GeoJSON layers. |
| **Frontend UI** | HTML5, CSS3, ES6 JS | Modular Vanilla ES6 | Fast, zero NPM build step required for core runtime, no heavy framework cold-start penalties. |
| **Containerization** | Docker | Multi-stage distroless/slim | Predictable container images, non-root execution, minimal attack surface. |
| **Cloud Hosting** | Google Cloud Run | Managed Serverless | Automatic scaling from 0 to N, native HTTPS, seamless integration with Cloud SQL and Secret Manager. |
| **Database Hosting** | Google Cloud SQL | PostgreSQL 15 | Managed backups, automated replication, Private Service Access VPC connectivity. |
| **Secret Management** | Google Secret Manager | v1 API | Complete decoupling of credentials from source code, Git, and Docker images. |
| **CI/CD** | Cloud Build / GitHub Actions | Declarative YAML | Automated linting, pytest suite execution, image building, and Cloud Run revision deployment. |
| **Testing** | pytest + pytest-cov | 8.0+ | Fast, expressive unit and integration test runner with code coverage reporting. |

---

## 2. Why Leaflet Over Commercial Maps JS?
1. **Cost & Autonomy**: Commercial map SDKs (Google Maps JS API, Mapbox) charge metered fees per map load and impose restrictive caching limits. Leaflet is 100% open source.
2. **Campus-Owned Data First**: Campus pathways, room polygons, and temporary obstacles are controlled directly by university facilities managers.
3. **Pluggable Tiles**: Leaflet can render OpenStreetMap, CARTO basemaps, or custom high-resolution campus orthophoto tile servers with zero vendor lock-in.

---

## 3. Why PostGIS Over Raw Lat/Lng Columns?
- Raw `(latitude, longitude)` float columns cannot perform spatial queries such as "find all facilities within building polygon `ST_Contains`", "find closest node within 20 meters `ST_DWithin`", or indexed nearest-neighbor search `ST_Distance` using spatial R-Tree / GIST indexes.
- PostGIS handles geographic ellipsoidal math (WGS84 / EPSG:4326) accurately, preventing spherical distortion at varying latitudes.
