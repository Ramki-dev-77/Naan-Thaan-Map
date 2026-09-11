# 07 — REST API Specification (OpenAPI v1)

All endpoints reside under `/api/v1` base path and return structured JSON with consistent schemas.

## 1. Response Envelope Format

### Standard Success Response:
```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "timestamp": "2026-09-11T12:00:00Z",
    "request_id": "req-18b3e8c9"
  }
}
```

### Standard Error Response:
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_COORDINATES",
    "message": "Origin latitude 95.2 is outside valid range [-90, 90].",
    "details": null
  },
  "meta": {
    "timestamp": "2026-09-11T12:00:00Z",
    "request_id": "req-18b3e8c9"
  }
}
```

---

## 2. Core Endpoints Summary

### 2.1 System Health
- `GET /health`: Process liveness check (HTTP 200 OK, no DB ping required).
- `GET /ready`: Application readiness check (verifies database connectivity).

### 2.2 Campuses & Map Data
- `GET /api/v1/campuses`: List all active campuses.
- `GET /api/v1/campuses/{id}`: Detailed metadata and boundary polygon for campus `{id}`.
- `GET /api/v1/campuses/{id}/map-data`: GeoJSON FeatureCollection containing all building footprints, entrance nodes, facilities, and walkway paths for single-trip map rendering.

### 2.3 Search
- `GET /api/v1/search?q={query}&campus_id={id}&category={cat}`:
  - Multi-attribute search across building names, codes, rooms, labs, and facilities.
  - Returns ranked list of matches with coordinates, floor, building metadata, and relevance score.

### 2.4 Routing Engine
- `POST /api/v1/routes`:
  - **Request Body**:
    ```json
    {
      "campus_id": 1,
      "origin": { "lat": 12.9716, "lng": 77.5946 },
      "destination": {
        "type": "room",
        "id": 14
      },
      "accessible": true
    }
    ```
  - **Response Body**:
    ```json
    {
      "status": "success",
      "data": {
        "route": {
          "total_distance_meters": 245.5,
          "estimated_duration_seconds": 188,
          "accessible": true,
          "geometry": {
            "type": "LineString",
            "coordinates": [[77.5946, 12.9716], [77.5949, 12.9719], ...]
          },
          "steps": [
            { "instruction": "Head northeast on Main Walkway toward CS Block", "distance_meters": 65 },
            { "instruction": "Turn right at Ramp to CS Block Entrance", "distance_meters": 25 },
            { "instruction": "Enter CS Block and take Elevator to Floor 2", "distance_meters": 15 },
            { "instruction": "Arrive at Artificial Intelligence Lab (CS-204)", "distance_meters": 0 }
          ]
        }
      }
    }
    ```

### 2.5 Facilities & Categories
- `GET /api/v1/categories`: List category filters with icons and colors.
- `GET /api/v1/facilities?campus_id={id}&category_id={cat_id}`: List facility markers.

### 2.6 Admin Endpoints (Authenticated)
- `POST /api/v1/admin/login`: Exchange credentials for authenticated session/token.
- `POST /api/v1/admin/logout`: Invalidate session.
- `POST /api/v1/admin/buildings`: Create building with footprint geometry.
- `PUT /api/v1/admin/buildings/{id}`: Update building metadata and geometry.
- `DELETE /api/v1/admin/buildings/{id}`: Delete building (soft delete or cascade with confirmation).
- `POST /api/v1/admin/rooms`: Create room/lab with floor and location coordinates.
- `POST /api/v1/admin/facilities`: Create facility point.
- `POST /api/v1/admin/nodes`: Create navigation node.
- `POST /api/v1/admin/edges`: Create navigation edge between two nodes.
- `GET /api/v1/admin/audit-logs`: Paginated audit log records.
