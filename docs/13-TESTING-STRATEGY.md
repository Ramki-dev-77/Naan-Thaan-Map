# 13 — Comprehensive Testing Strategy

## 1. Test Pyramid & Automation Framework
Quality assurance uses a multi-tier testing strategy managed via `pytest` and `pytest-cov`:

```
                 ▲
                / \
               /   \      E2E Integration Tests (API + Frontend journeys)
              /-----\
             /       \    API Contract Tests (Flask test client)
            /---------\
           /           \  Domain Unit Tests (A* Routing, Search Ranking, Geometry)
          ───────────────
```

---

## 2. Test Suites & Coverage Focus Areas

### 2.1 Routing Engine Test Suite (`tests/test_routing.py`)
- **Direct Path**: Pathfinding between two adjacent nodes connected by a single walkway edge.
- **Multi-Hop Traversal**: Multi-node navigation across buildings and pedestrian intersections.
- **Accessibility Filtering**: Verifies that requesting `accessible=True` strictly excludes edges with `stairs=True` and redirects navigation through ramps/elevators.
- **Blocked Path / Graph Partition**: Verifies graceful error response when start and destination exist on disconnected graph partitions.
- **Nearest Node Snapping**: Correctly identifies the closest navigation node within threshold radius and rejects coordinates beyond 100m outside the campus boundary.

### 2.2 Search Service Test Suite (`tests/test_search.py`)
- **Exact Matches**: Querying "CSB" finds "Computer Science Block".
- **Prefix Matches**: Querying "CS" matches "CS-101", "CS-102", "CS-LAB-1".
- **Fuzzy / Substring Matches**: Querying "Lab" returns all laboratories across departments.
- **Category Filtering**: Querying with `category="Dining"` returns only cafeterias and food stalls.

### 2.3 API Contract Tests (`tests/test_api.py`)
- `GET /health` returns HTTP 200 with status "ok".
- `GET /ready` verifies the static JSON data store is loaded and returns HTTP 200.
- `GET /api/v1/campuses/{id}/map-data` returns valid GeoJSON FeatureCollection with required properties (`name`, `category`, `building_id`).
- Error envelope structure compliance on 404, 400, and 422 conditions.

### 2.4 Geolocation UX Tests (`tests/test_geolocation.py`)
- Accuracy classification rules validation:
  - 8m → `EXCELLENT`
  - 18m → `GOOD`
  - 35m → `USABLE`
  - 75m → `APPROXIMATE`
  - 150m → `POOR`
- Velocity filter clamps sudden teleportation jumps.

### 2.5 Security & Admin Access Tests (`tests/test_admin.py`)
- Unauthorized requests to `/api/v1/admin/*` are blocked with HTTP 401/403.
- Successful login grants authenticated session cookie.
- Password hashing prevents cleartext storage.
- Administrative entity creation correctly appends an immutable `AuditLog` row.
