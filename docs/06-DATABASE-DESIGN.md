# 06 — Database Design & Spatial Schema

## 1. Relational & Geospatial Schema Diagram

```
┌──────────────────┐       ┌──────────────────────┐       ┌──────────────────┐
│     campuses     │1     *│      buildings       │1     *│      rooms       │
├──────────────────┤───────├──────────────────────┤───────├──────────────────┤
│ id (UUID/PK)     │       │ id (UUID/PK)         │       │ id (UUID/PK)     │
│ name             │       │ campus_id (FK)       │       │ building_id (FK) │
│ slug (UNIQUE)    │       │ name                 │       │ room_number      │
│ description      │       │ code (UNIQUE)        │       │ name             │
│ location (POINT) │       │ description          │       │ floor (INT)      │
│ boundary (POLY)  │       │ location (POINT)     │       │ description      │
│ created_at       │       │ footprint (POLYGON)  │       │ location (POINT) │
└──────────────────┘       │ created_at           │       │ node_id (FK,opt) │
         │1                └──────────────────────┘       └──────────────────┘
         │                            │1
         │                            │* (optional)
         │*                           ▼
┌──────────────────┐       ┌──────────────────────┐
│    facilities    │*     1│      categories      │
├──────────────────┤───────├──────────────────────┤
│ id (UUID/PK)     │       │ id (UUID/PK)         │
│ campus_id (FK)   │       │ name (UNIQUE)        │
│ building_id (FK) │       │ slug                 │
│ category_id (FK) │       │ icon                 │
│ name             │       │ color                │
│ description      │       └──────────────────────┘
│ location (POINT) │
└──────────────────┘

┌──────────────────────────────┐          ┌──────────────────────────────┐
│       navigation_nodes       │1        *│       navigation_edges       │
├──────────────────────────────┤──────────├──────────────────────────────┤
│ id (UUID/PK)                 │          │ id (UUID/PK)                 │
│ campus_id (FK)               │          │ source_node_id (FK)          │
│ building_id (FK, nullable)   │          │ destination_node_id (FK)     │
│ node_type                    │          │ distance (FLOAT, meters)     │
│ floor (INT, default 0)       │          │ accessible (BOOLEAN)         │
│ location (POINT, SRID 4326)  │          │ stairs (BOOLEAN)             │
│ is_active (BOOLEAN)          │          │ path_type (WALKWAY,RAMP,etc) │
└──────────────────────────────┘          │ is_bidirectional (BOOLEAN)   │
                                          └──────────────────────────────┘

┌──────────────────────────────┐          ┌──────────────────────────────┐
│         admin_users          │1        *│          audit_logs          │
├──────────────────────────────┤──────────├──────────────────────────────┤
│ id (UUID/PK)                 │          │ id (UUID/PK)                 │
│ username (UNIQUE)            │          │ admin_id (FK, nullable)      │
│ email (UNIQUE)               │          │ action (CREATE,UPDATE,DELETE)│
│ password_hash                │          │ entity_type                  │
│ role (ADMIN, SUPERADMIN)     │          │ entity_id                    │
│ is_active                    │          │ metadata (JSONB)             │
│ last_login                   │          │ ip_address                   │
│ created_at                   │          │ created_at                   │
└──────────────────────────────┘          └──────────────────────────────┘
```

---

## 2. Model Field Specifications

### 2.1 `Campus`
- `id`: Primary key (UUID/String or Integer auto-increment).
- `name`: Full title (e.g., "Apex Institute of Technology — Main Campus").
- `slug`: URL-friendly unique identifier (e.g., "apex-main").
- `description`: Textual summary.
- `location`: `Geometry(Point, srid=4326)` representing campus centroid.
- `boundary`: `Geometry(Polygon, srid=4326)` representing campus legal boundary.
- `created_at` / `updated_at`: UTC timestamps.

### 2.2 `Building`
- `id`: Primary key.
- `campus_id`: Foreign key to `campuses.id`.
- `name`: E.g., "Computer Science Block".
- `code`: Unique code per campus (e.g., "CSB").
- `description`: Notes on departments housed, accessibility features.
- `location`: Centroid point `Geometry(Point, srid=4326)`.
- `footprint`: Building outline `Geometry(Polygon, srid=4326)`.
- `floors_above`: Number of stories (e.g., 4).
- `floors_below`: Basement stories (e.g., 0).

### 2.3 `Room`
- `id`: Primary key.
- `building_id`: Foreign key to `buildings.id`.
- `room_number`: E.g., "CS-101", "204".
- `name`: E.g., "Artificial Intelligence Research Lab".
- `floor`: Integer floor index (0 = Ground, 1 = First Floor, etc.).
- `description`: Equipment, capacity, or office occupant.
- `location`: Point coordinate `Geometry(Point, srid=4326)`.
- `node_id`: Optional FK to the specific doorway `NavigationNode`.

### 2.4 `Facility`
- `id`: Primary key.
- `campus_id`: Foreign key to `campuses.id`.
- `building_id`: Nullable foreign key (null if outdoor landmark/parking).
- `category_id`: Foreign key to `categories.id`.
- `name`: E.g., "Main Cafeteria", "Emergency Health Center", "North Parking Gate".
- `description`: Hours of operation, services offered.
- `location`: Point coordinate `Geometry(Point, srid=4326)`.

### 2.5 `Category`
- `id`: Primary key.
- `name`: E.g., "Academic", "Dining", "Parking", "Restroom", "Medical", "Administrative".
- `slug`: Unique slug string.
- `icon`: Icon identifier (e.g., "book", "coffee", "car", "cross", "restroom").
- `color`: Hex color string for UI rendering (e.g., `#2563eb`).

### 2.6 `NavigationNode`
- `id`: Primary key.
- `campus_id`: Foreign key to `campuses.id`.
- `building_id`: Nullable foreign key.
- `node_type`: Enum string (`ENTRANCE`, `WALKWAY_JUNCTION`, `STAIRS`, `RAMP`, `ELEVATOR`, `ROOM_DOOR`).
- `floor`: Integer floor level (0 for outdoor ground paths).
- `location`: Point coordinate `Geometry(Point, srid=4326)`.
- `is_active`: Boolean flag allowing path closures during construction.

### 2.7 `NavigationEdge`
- `id`: Primary key.
- `source_node_id`: Foreign key to `navigation_nodes.id`.
- `destination_node_id`: Foreign key to `navigation_nodes.id`.
- `distance`: Distance in meters (calculated via `ST_Distance` on WGS84 geography or computed).
- `accessible`: Boolean (`true` if wheelchair/stroller accessible, `false` if stairs).
- `stairs`: Boolean (`true` if this edge contains stairs).
- `path_type`: Enum string (`PAVED_WALKWAY`, `CORRIDOR`, `RAMP`, `STAIRWAY`, `ELEVATOR`).
- `is_bidirectional`: Boolean (default `true` for standard walkways).

---

## 3. Spatial & Search Indexing Strategy
1. **Spatial Indexes (GIST)**:
   - `CREATE INDEX idx_campus_boundary ON campuses USING GIST (boundary);`
   - `CREATE INDEX idx_building_footprint ON buildings USING GIST (footprint);`
   - `CREATE INDEX idx_nav_node_location ON navigation_nodes USING GIST (location);`
   - `CREATE INDEX idx_facility_location ON facilities USING GIST (location);`
2. **Text Search Indexes (GIN Trigram / B-Tree)**:
   - `CREATE INDEX idx_building_name_trgm ON buildings USING GIN (name gin_trgm_ops);`
   - `CREATE INDEX idx_room_name_trgm ON rooms USING GIN (name gin_trgm_ops);`
   - `CREATE INDEX idx_facility_name_trgm ON facilities USING GIN (name gin_trgm_ops);`
