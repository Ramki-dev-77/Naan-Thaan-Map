# 09 — Map & Routing Architecture (Campus Pedestrian Graph & A* Search)

## 1. Multi-Layer Routing Architecture

The system segregates routing into two distinct domains:

1. **Layer 1: Campus Pedestrian Graph (Internal)**
   - Operates entirely within the campus boundaries on university-maintained pathways, ramps, building doorways, corridors, stairs, and elevator shafts.
   - Powered by an in-memory spatial graph loaded from `NavigationNode` and `NavigationEdge` database models.
   - Uses the **A* (A-Star) search algorithm** with Haversine distance heuristic.
   - Cost function incorporates physical distance plus penalization terms (stairs, surface roughness, accessibility constraints).

2. **Layer 2: External Routing Provider (Boundary Fallback)**
   - Placed behind a generic `RoutingProvider` interface.
   - Invoked only if origin and destination span across public external city roads outside the campus boundary.
   - Implementation: `CampusRoutingService` (default) and `GoogleExternalRoutingService` (optional fallback).

---

## 2. Pedestrian Graph Modeling

```
 [Main Entrance Node]
         │
         │ (Walkway Edge: 45m, accessible=True)
         ▼
 [Plaza Junction Node] ────────────── (Ramp Edge: 20m, accessible=True) ──────────────► [CS Block Entrance]
         │                                                                                       │
         │ (Stairs Edge: 12m,                                                                    │ (Indoor Corridor: 15m)
         │  accessible=False,                                                                    ▼
         │  stairs=True)                                                                  [Elevator Node Floor 0]
         ▼                                                                                       │
 [Courtyard Lower Node]                                                                          │ (Vertical Transit: 4m)
                                                                                                 ▼
                                                                                          [Elevator Node Floor 2]
                                                                                                 │
                                                                                                 │ (Corridor: 25m)
                                                                                                 ▼
                                                                                          [CS-LAB-2 Door Node]
```

### Graph Components:
- **`NavigationNode`**: Geographic coordinate `(latitude, longitude)`, optional `building_id`, `floor`, and `node_type` (`ENTRANCE`, `JUNCTION`, `STAIRS`, `ELEVATOR`, `DOOR`).
- **`NavigationEdge`**: Directed or bidirectional connection with:
  - `distance_meters`: True geodesic distance.
  - `accessible`: Boolean flag (true for flat pavement, ramps, elevators; false for stairs).
  - `stairs`: Boolean indicator.
  - `weight`: Calculated traversal cost.

---

## 3. The A* Pathfinding Algorithm

The A* algorithm evaluates candidate nodes using the evaluation function:
$$f(n) = g(n) + h(n)$$
Where:
- $g(n)$ is the exact accumulated cost from start node to node $n$.
- $h(n)$ is the heuristic admissible estimate of the cost from node $n$ to the goal node (Haversine great-circle distance).

### Cost Function & Accessibility Penalty:
For each edge $e = (u, v)$ with physical length $L$:
$$g(v) = g(u) + L \times \text{CostMultiplier}(e)$$

- **Standard Pedestrian Mode**:
  - Paved walkway: Multiplier = $1.0$
  - Ramps: Multiplier = $1.05$
  - Stairs: Multiplier = $1.8$ (pedestrians generally prefer level walks over climbing stairs)
- **Accessible Mode (`accessible=true`)**:
  - Paved walkway: Multiplier = $1.0$
  - Ramps / Elevators: Multiplier = $1.0$
  - Stairs: Multiplier = $\infty$ (strictly pruned from path search)

---

## 4. Nearest Node Snapping
When a user requests a route from arbitrary coordinates $(lat, lng)$, the system:
1. Calculates the geodesic distance to all active `NavigationNode` records within a 100-meter search radius.
2. Snaps origin to the closest walkable node.
3. If no node exists within 100m (user is off-campus), returns an explicit error prompting the user to select a campus entrance as the start point.

---

## 5. Recalculation Trigger (Off-Route Detection)
During active navigation:
- As position updates stream from `geolocation.js`, the distance from the user's smoothed coordinates to the nearest segment of the current route polyline is computed via point-to-line-segment projection.
- **Threshold**: If perpendicular deviation exceeds **25 meters** for two consecutive fixes, the UI triggers an automatic route recalculation from the user's new position.
