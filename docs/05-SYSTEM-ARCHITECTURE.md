# 05 — System Architecture & Component Design

## 1. High-Level Architecture Diagram

```
                 ┌───────────────────────────────────────────┐
                 │                Client Tier                │
                 │   Desktop / Tablet / Mobile Smartphone    │
                 └─────────────────────┬─────────────────────┘
                                       │ HTTPS / W3C Geolocation
                                       ▼
                 ┌───────────────────────────────────────────┐
                 │           Google Cloud Load Balancer      │
                 │              Cloud CDN / SSL Edge         │
                 └─────────────────────┬─────────────────────┘
                                       │
                                       ▼
                 ┌───────────────────────────────────────────┐
                 │           Compute Tier (Cloud Run)        │
                 │      Gunicorn WSGI Master + Sync Workers  │
                 │                                           │
                 │  ┌─────────────────────────────────────┐  │
                 │  │          Flask App Factory          │  │
                 │  │  - Rate Limiting (Flask-Limiter)    │  │
                 │  │  - Security Headers & CSRF          │  │
                 │  │  - Structured JSON Logging          │  │
                 │  │  - Health Checks (/health, /ready)  │  │
                 │  └──────────────────┬──────────────────┘  │
                 │                     │                     │
                 │      ┌──────────────┴──────────────┐      │
                 │      ▼                             ▼      │
                 │  ┌──────────────┐          ┌────────────┐ │
                 │  │ API Handlers │          │ Admin Web  │ │
                 │  │  (v1 REST)   │          │ (Jinja/UI) │ │
                 │  └──────┬───────┘          └─────┬──────┘ │
                 │         │                        │        │
                 │         ▼                        │        │
                 │  ┌─────────────────────────────┐ │        │
                 │  │       Service Layer         │ │        │
                 │  │  - SearchService            │ │        │
                 │  │  - CampusRoutingService(A*) ◄─────────┘│
                 │  │  - LocationAccuracyService  │          │
                 │  │  - AdminAuditService        │          │
                 │  └──────────────┬──────────────┘          │
                 └─────────────────┼─────────────────────────┘
                                   │ Private VPC Peering
                                   ▼
                 ┌───────────────────────────────────────────┐
                 │        Data Tier (Cloud SQL PostgreSQL)   │
                 │               PostGIS 3.3+                │
                 │                                           │
                 │  - Campuses, Buildings, Footprints (Poly) │
                 │  - Rooms, Facilities, Entrances (Point)   │
                 │  - NavigationNodes (Point)                │
                 │  - NavigationEdges (LineString + Weights) │
                 │  - Spatial GIST & Trigram GIN Indexes     │
                 └───────────────────────────────────────────┘
```

---

## 2. Layered Component Responsibilities

### 2.1 Presentation Layer (Frontend)
- **Map Renderer (`map.js`)**: Manages Leaflet canvas, GeoJSON feature loading, layer filtering, building focus, and visual path polylines.
- **Search Controller (`search.js`)**: Handles user input with 300ms debouncing, initiates `/api/v1/search` queries, renders result cards, and stages navigation destinations.
- **Geolocation Controller (`geolocation.js`)**: Encapsulates `navigator.geolocation.watchPosition`, categorizes accuracy into UX badges, runs smoothing filters, and alerts users upon indoor attenuation.
- **Navigation Controller (`navigation.js`)**: Orchestrates origin/destination states, executes route requests, computes walking times, displays turn-by-turn guidance, and triggers recalculation if deviation exceeds 25m.

### 2.2 Application / API Layer (Flask)
- **Application Factory (`create_app`)**: Initializes extensions, registers blueprints, binds security middlewares, and configures environment-specific settings.
- **Versioned API Blueprints (`api/v1/`)**: REST endpoints for campuses, buildings, search, routing, and facilities.
- **Admin Blueprint (`admin/`)**: Session-authenticated management interface with CSRF-protected forms and audit logging.

### 2.3 Service Layer
- **`RoutingService`**: Graph traversal engine executing A* search on nodes and edges with distance calculations, barrier checking, and accessibility filters (`accessible=True`).
- **`SearchService`**: PostgreSQL trigram/tsvector queries ranking results by exact match, prefix match, and category relevance.
- **`LocationService`**: Coordinate snapping to nearest pedestrian node within radius thresholds.
- **`AuditService`**: Asynchronous/transactional logging of administrative actions into `AuditLog`.

### 2.4 Data Tier (PostgreSQL + PostGIS)
- Stores spatial geometries in WGS84 (SRID 4326).
- GIST spatial indexes on `location`, `footprint`, and `boundary` columns.
- Trigram GIN indexes on search text attributes for sub-second text matching.
