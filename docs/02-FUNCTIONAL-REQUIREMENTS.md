# 02 — Functional Requirements Specification

## 1. Interactive Campus Map
- **FR-MAP-001**: Interactive Leaflet-based vector/raster canvas with panning, pinch-to-zoom, and smooth bounds fitting.
- **FR-MAP-002**: Multi-layer visualization:
  - Campus boundary polygon with clear perimeter stroke.
  - Building footprint polygons with hover tooltip and click-to-focus behavior.
  - Verified building entrance markers with icon indicators.
  - Campus facilities (cafeterias, medical clinic, parking, restrooms, library, ATM).
  - Calculated pedestrian route polyline.
  - User position circle with translucent accuracy uncertainty radius.
- **FR-MAP-003**: Dynamic category layer toggling (e.g. show/hide Parking, Dining, Academic, Restrooms).
- **FR-MAP-004**: Responsive mobile viewport orientation handling with persistent quick-action controls.

---

## 2. Multi-Attribute Intelligent Search
- **FR-SRC-001**: High-speed search supporting:
  - Building names (e.g., "Computer Science Block", "Central Library")
  - Building codes (e.g., "CSB", "LIB", "ADM")
  - Room identifiers (e.g., "CS-101", "Room 204", "AI Lab")
  - Department and administrative offices (e.g., "Dean Office", "Registrar")
  - Facility categories (e.g., "Food", "Parking", "Medical", "Washroom")
- **FR-SRC-002**: Tiered ranking algorithm:
  1. Exact identifier match
  2. Prefix match
  3. Substring match across names, aliases, and department metadata
  4. Trigram / fuzzy phonetic match
- **FR-SRC-003**: Client-side debouncing (300 ms) to conserve network bandwidth and backend compute.
- **FR-SRC-004**: Clicking a search result centers the map, opens the destination card, and stages it for immediate navigation.

---

## 3. Campus Pedestrian Routing Engine
- **FR-ROU-001**: Origin selection:
  - "Current Location" via browser Geolocation API.
  - "Choose on Map" / Manual search selection (for planning or indoor GPS fallback).
- **FR-ROU-002**: Destination selection:
  - Any verified room, building entrance, or outdoor facility.
- **FR-ROU-003**: Graph route calculation:
  - Snaps origin and destination coordinates to nearest valid campus `NavigationNode`.
  - Executes A* algorithm over the `NavigationEdge` graph.
  - Computes total distance in meters and walking duration at average walking speed (1.3 m/s).
- **FR-ROU-004**: Accessibility routing:
  - When `accessible=true` flag is set, excludes edges marked `stairs=true` or exceeding slope thresholds, prioritizing ramps and elevators.
  - If no fully accessible path exists, returns an explicit warning rather than routing through stairs.
- **FR-ROU-005**: Step-by-step turn guidance generator producing human-readable directives.
- **FR-ROU-006**: Route recalculation logic triggering when moving user deviates > 25 meters from the established path.

---

## 4. Location & Accuracy Management
- **FR-LOC-001**: Explicit permission request upon clicking "My Location" or "Navigate".
- **FR-LOC-002**: High accuracy mode requested (`enableHighAccuracy: true`, `timeout: 10000`, `maximumAge: 5000`).
- **FR-LOC-003**: Categorized accuracy badge:
  - `≤ 10 m`: Excellent
  - `10 – 25 m`: Good
  - `25 – 50 m`: Usable
  - `50 – 100 m`: Approximate
  - `> 100 m`: Poor
- **FR-LOC-004**: Sensor jitter smoothing discarding unreasonable jumps (> 50 m in < 1 second).
- **FR-LOC-005**: Graceful fallback banner upon permission denial or indoor attenuation.

---

## 5. Administration & Governance
- **FR-ADM-001**: Authenticated admin login with session protection and brute-force rate limiting.
- **FR-ADM-002**: Multi-campus management (create, update bounds, set active campus).
- **FR-ADM-003**: Building and room CRUD with footprint geometry and floor assignments.
- **FR-ADM-004**: Facility and category management with icon/color selection.
- **FR-ADM-005**: Navigation graph editor: create/connect nodes and edges with accessibility flags.
- **FR-ADM-006**: Immutable audit logging recording admin user, action, target entity, timestamp, and IP address.
