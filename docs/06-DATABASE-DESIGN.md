# 06 — Static JSON Data Design

The application has no database schema, migrations, database connection, or runtime data writes. Bundled JSON files under `app/data/` are the source of truth and are loaded into memory when the Flask application starts.

## 1. Data Files

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
| File | Contents |
|---|---|
| `campuses.json` | Campus identity, centroid, and boundary polygons. |
| `buildings.json` | Campus/building IDs, coordinates, footprints, entrances, and accessibility. |
| `rooms.json` | Building IDs, room identity, floor, coordinates, and associated graph node IDs. |
| `facilities.json` | Campus/building/category IDs, point coordinates, and descriptions. |
| `categories.json` | Facility category names, slugs, icons, and colors. |
| `svce_network.json` | Primary SVCE walking graph as `nodes` and `edges`; node IDs and edge endpoints are the graph references. |
| `demo_network.json` | Demo campus graph kept separate from the SVCE graph data. |
| `admins.json` | Admin identities and password hashes used by the existing admin login. |

Coordinates use GeoJSON order `[longitude, latitude]` in geometries and named `latitude`/`longitude` fields on entities. `LocationService` combines the entities into the existing map-data FeatureCollection. `RoutingService` resolves destinations through room/building/facility/node IDs, snaps coordinates to a graph node, and runs the existing A* pathfinder over the static edges.

## 2. Editing and Deployment
Edit the JSON files directly, validate them with `flask --app run.py validate-data`, then redeploy the application. Admin changes performed through the live process are in-memory only and are not saved to these files; they do not persist across restarts or serverless instances.
### 2.4 `Facility`
