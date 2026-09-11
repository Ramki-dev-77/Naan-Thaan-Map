# 17 — Data Import, Seed Tooling & Admin Operations

## 1. Automated Seed Tooling (`flask seed-demo`)
To initialize local or staging instances with a verified, realistic campus spatial dataset, the application provides an idempotent Flask CLI command:

```bash
flask seed-demo --campus-name "Apex Institute of Technology — Main Campus"
```

### Generated Seed Dataset:
- **Campus Perimeter**: Realistic multi-hectare closed polygon boundary with centroid coordinates.
- **6 Primary Buildings**:
  1. **Administration Block (ADM)**: Registrar, Dean of Academic Affairs, Admissions.
  2. **Computer Science & Engineering Block (CSB)**: CS-101, CS-102, AI Lab, Robotics Lab, Systems Lab.
  3. **Electronics & Electrical Engineering Block (EEB)**: Circuits Lab, VLSI Research Lab, Faculty Cabins.
  4. **Central Library & Innovation Hub (LIB)**: Digital Archives, Study Halls, Maker Space.
  5. **Student Activity Center (SAC)**: Main Food Court, Indoor Sports, Student Clubs.
  6. **Main University Auditorium (AUD)**: 1,500-seat plenary hall.
- **Facilities & Points of Interest**:
  - Main Security Gate & Checkpoint
  - North Parking Lot & EV Charging Station
  - Campus Health & Urgent Medical Center
  - Central Cafeteria & Coffee Kiosk
  - Restroom Blocks (Wheelchair accessible)
  - ATM Kiosks
- **Pedestrian Network**:
  - 40+ Navigation Nodes (walkway junctions, building doorways, ramps, staircases).
  - 60+ Directional and Bidirectional Edges with true geodesic distances in meters and explicit accessibility flags (`accessible: true/false`, `stairs: true/false`).

---

## 2. GeoJSON Data Ingestion Pipeline
Campus facility managers can import GIS shapefiles or GeoJSON boundaries directly:
```bash
flask import-geojson --type=buildings --file=data/campuses/apex_buildings.geojson
flask import-geojson --type=network --file=data/campuses/apex_pedestrian_network.geojson
```

### Data Validation Rules:
1. All coordinates must be valid EPSG:4326 (`longitude: [-180, 180]`, `latitude: [-90, 90]`).
2. Building polygon geometries must be closed rings with positive area.
3. Every `Room` must map to an existing `Building` and have a valid integer floor.
4. Navigation network must be verified for graph connectivity (zero orphaned nodes).
