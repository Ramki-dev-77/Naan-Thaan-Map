"""
Campus Navigation System — Routing Engine
Implements the Campus Pedestrian Graph and A* Pathfinding Algorithm with
accessibility constraints, nearest-node snapping, and turn-by-turn instruction generation.
"""
import math
import heapq
from typing import List, Dict, Tuple, Optional, Any
from app.models.navigation import NavigationNode, NavigationEdge
from app.models.building import Building
from app.models.room import Room
from app.models.facility import Facility
from app.utils.errors import AppError


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth in meters.
    """
    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate initial compass bearing from point 1 to point 2 in degrees [0, 360)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def bearing_to_direction(bearing: float) -> str:
    """Convert bearing degrees into cardinal directions."""
    directions = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
    idx = round(bearing / 45.0) % 8
    return directions[idx]


class RoutingProviderInterface:
    """Abstract interface for routing engines."""
    def calculate_route(self, origin: Dict[str, float], destination: Dict[str, Any], accessible: bool = False) -> Dict[str, Any]:
        raise NotImplementedError


class CampusPedestrianRoutingService(RoutingProviderInterface):
    """
    In-memory graph pathfinder using A* search over campus NavigationNode
    and NavigationEdge entities.
    """

    AVERAGE_WALKING_SPEED_MPS = 1.3  # 1.3 meters per second (~4.7 km/h)

    @classmethod
    def snap_to_nearest_node(cls, campus_id: int, lat: float, lng: float, max_radius_meters: float = 800.0) -> NavigationNode:
        """Find the physically closest navigation node on the campus network."""
        nodes = NavigationNode.query.filter_by(campus_id=campus_id, is_active=True).all()
        if not nodes:
            raise AppError("No navigation network available for this campus.", code="NO_NETWORK_NODES", status_code=404)

        closest_node = None
        min_dist = float("inf")

        for node in nodes:
            dist = haversine_distance(lat, lng, node.latitude, node.longitude)
            if dist < min_dist:
                min_dist = dist
                closest_node = node

        if min_dist > max_radius_meters:
            raise AppError(
                f"Selected origin is {round(min_dist)}m away from campus network (max {int(max_radius_meters)}m). Please choose a starting point on campus.",
                code="ORIGIN_OUTSIDE_CAMPUS",
                status_code=400,
            )

        return closest_node

    @classmethod
    def find_optimal_path(cls, campus_id: int, start_node_id: int, target_node_id: int, accessible_only: bool = False, mode: str = "fastest") -> Tuple[List[NavigationNode], float]:
        """
        Executes A* search from start_node_id to target_node_id.
        Supports modes: 'fastest', 'accessible', 'main_avenue'.
        Returns (node_sequence, total_physical_distance_meters).
        """
        if start_node_id == target_node_id:
            node = NavigationNode.get(start_node_id)
            return ([node] if node else []), 0.0

        # Load all active nodes and edges for this campus
        nodes_dict = {n.id: n for n in NavigationNode.query.filter_by(campus_id=campus_id, is_active=True).all()}
        if start_node_id not in nodes_dict or target_node_id not in nodes_dict:
            raise AppError("Start or target navigation node is not active or recognized.", code="NODE_NOT_FOUND", status_code=404)

        target_node = nodes_dict[target_node_id]

        # Build adjacency graph
        all_edges = NavigationEdge.query.all()
        edges = [e for e in all_edges if e.source_node and e.source_node.campus_id == campus_id]

        adj: Dict[int, List[Tuple[int, float, bool, bool, str]]] = {nid: [] for nid in nodes_dict}

        is_accessible_mode = (mode == "accessible" or accessible_only)

        for edge in edges:
            if edge.source_node_id in adj and edge.destination_node_id in nodes_dict:
                # If accessible routing is requested, discard stairs completely
                if is_accessible_mode and (edge.stairs or not edge.accessible):
                    continue
                
                # Weight calculation depending on selected routing mode
                weight = edge.distance
                if mode == "fastest":
                    if edge.stairs:
                        weight *= 1.2  # Slight pedestrian cost for stairs, but available for shortcuts
                elif mode == "main_avenue":
                    if edge.stairs:
                        weight *= 12.0  # Strongly avoid stairs
                    if edge.path_type == "MAIN_AVENUE":
                        weight *= 0.65  # High priority for wide, tree-lined avenues
                    elif edge.path_type == "PAVED_WALKWAY":
                        weight *= 0.95
                    else:
                        weight *= 2.2  # Avoid narrow side-paths or stairs
                elif is_accessible_mode:
                    if edge.path_type == "RAMP":
                        weight *= 0.9  # Prefer well-built ramps

                adj[edge.source_node_id].append((edge.destination_node_id, weight, edge.accessible, edge.stairs, edge.path_type))

                if edge.is_bidirectional and edge.destination_node_id in adj:
                    adj[edge.destination_node_id].append((edge.source_node_id, weight, edge.accessible, edge.stairs, edge.path_type))

        # A* priority queue: (f_score, current_g_score, current_node_id)
        open_set = []
        start_h = haversine_distance(nodes_dict[start_node_id].latitude, nodes_dict[start_node_id].longitude,
                                     target_node.latitude, target_node.longitude)
        heapq.heappush(open_set, (start_h, 0.0, start_node_id))

        came_from: Dict[int, int] = {}
        g_scores: Dict[int, float] = {nid: float("inf") for nid in nodes_dict}
        g_scores[start_node_id] = 0.0

        visited = set()

        while open_set:
            f, current_g, current_id = heapq.heappop(open_set)

            if current_id == target_node_id:
                # Reconstruct path
                path = []
                curr = current_id
                while curr in came_from:
                    path.append(nodes_dict[curr])
                    curr = came_from[curr]
                path.append(nodes_dict[start_node_id])
                path.reverse()

                # Calculate true physical distance along path in meters
                physical_dist = 0.0
                for i in range(len(path) - 1):
                    physical_dist += haversine_distance(path[i].latitude, path[i].longitude,
                                                        path[i + 1].latitude, path[i + 1].longitude)
                return path, max(physical_dist, 1.0)

            if current_id in visited:
                continue
            visited.add(current_id)

            for neighbor_id, weight, is_acc, has_stairs, ptype in adj.get(current_id, []):
                tentative_g = current_g + weight
                if tentative_g < g_scores[neighbor_id]:
                    came_from[neighbor_id] = current_id
                    g_scores[neighbor_id] = tentative_g
                    h = haversine_distance(nodes_dict[neighbor_id].latitude, nodes_dict[neighbor_id].longitude,
                                           target_node.latitude, target_node.longitude)
                    heapq.heappush(open_set, (tentative_g + h, tentative_g, neighbor_id))

        # If we reached here, no path was found
        if is_accessible_mode:
            raise AppError(
                "No step-free accessible route found between these locations. An obstacle (stairs) exists on all paths.",
                code="NO_ACCESSIBLE_ROUTE",
                status_code=422,
            )
        raise AppError(
            "No connecting walkable path found between origin and destination on this campus graph.",
            code="ROUTE_NOT_FOUND",
            status_code=404,
        )

    @classmethod
    def generate_turn_instructions(cls, path: List[NavigationNode], destination_label: str) -> List[Dict[str, Any]]:
        """Generate human-readable step-by-step pedestrian directions from node sequence."""
        if not path or len(path) < 2:
            return [{
                "instruction": f"You are already at {destination_label}.",
                "distance_meters": 0,
                "node_type": "DOOR",
                "floor": path[0].floor if path else 0
            }]

        steps = []
        for i in range(len(path) - 1):
            curr = path[i]
            nxt = path[i + 1]
            seg_dist = haversine_distance(curr.latitude, curr.longitude, nxt.latitude, nxt.longitude)
            bearing = calculate_bearing(curr.latitude, curr.longitude, nxt.latitude, nxt.longitude)
            direction = bearing_to_direction(bearing)

            # Contextual instructions based on node types
            if nxt.node_type == "ENTRANCE":
                instr = f"Head {direction} towards {nxt.label or 'Building Entrance'}"
            elif nxt.node_type == "STAIRS":
                instr = f"Proceed {direction} to stairs and continue to floor {nxt.floor}"
            elif nxt.node_type == "ELEVATOR":
                instr = f"Take elevator to floor {nxt.floor}"
            elif nxt.node_type == "RAMP":
                instr = f"Use accessible ramp heading {direction}"
            elif i == len(path) - 2:
                instr = f"Arrive at destination: {destination_label}"
            else:
                instr = f"Continue {direction} on walkway towards {nxt.label or 'junction'}"

            steps.append({
                "instruction": instr,
                "distance_meters": round(seg_dist, 1),
                "node_type": nxt.node_type,
                "floor": nxt.floor,
            })

        return steps


class ExternalGoogleRoutingService(RoutingProviderInterface):
    """
    Stub external provider integration for Google Maps Routes API.
    Used when routing outside of the campus-internal pedestrian graph.
    """
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def calculate_route(self, origin: Dict[str, float], destination: Dict[str, Any], accessible: bool = False) -> Dict[str, Any]:
        # Production Google Routes API integration interface
        raise NotImplementedError("External Google Routes API integration is configured for off-campus navigation only.")


class RoutingService:
    """Unified routing service facade."""
    pedestrian_service = CampusPedestrianRoutingService()

    @classmethod
    def calculate_campus_route(cls, campus_id: int, origin_coords: Dict[str, float], destination_info: Dict[str, Any], accessible: bool = False) -> Dict[str, Any]:
        """
        Coordinates origin snapping, target node identification, A* multi-path calculation,
        and response formatting with alternative route choices.
        """
        # 1. Snap origin to closest campus node
        orig_lat = origin_coords.get("lat")
        orig_lng = origin_coords.get("lng")
        dest_lat = None
        dest_lng = None

        start_node = cls.pedestrian_service.snap_to_nearest_node(
            campus_id=campus_id,
            lat=orig_lat,
            lng=orig_lng
        )

        # 2. Resolve target node
        dest_type = destination_info.get("type")
        dest_id = destination_info.get("id")
        target_node = None
        destination_label = "Destination"

        if dest_type == "room":
            room = Room.get(dest_id)
            if not room:
                raise AppError("Destination room not found.", code="DESTINATION_NOT_FOUND", status_code=404)
            destination_label = f"{room.room_number} — {room.name}"
            dest_lat = room.latitude or (room.building.latitude if room.building else None)
            dest_lng = room.longitude or (room.building.longitude if room.building else None)
            # If room has specific door node, use it; otherwise use building entrance
            if room.node_id:
                target_node = NavigationNode.get(room.node_id)
            if not target_node and room.building:
                target_node = NavigationNode.query.filter_by(building_id=room.building_id, node_type="ENTRANCE").first()
                if not target_node:
                    target_node = cls.pedestrian_service.snap_to_nearest_node(
                        campus_id=campus_id,
                        lat=room.building.entrance_latitude or room.building.latitude,
                        lng=room.building.entrance_longitude or room.building.longitude
                    )

        elif dest_type == "building":
            building = Building.get(dest_id)
            if not building:
                raise AppError("Destination building not found.", code="DESTINATION_NOT_FOUND", status_code=404)
            destination_label = building.name
            dest_lat = building.entrance_latitude or building.latitude
            dest_lng = building.entrance_longitude or building.longitude
            target_node = NavigationNode.query.filter_by(building_id=building.id, node_type="ENTRANCE").first()
            if not target_node:
                target_node = cls.pedestrian_service.snap_to_nearest_node(
                    campus_id=campus_id,
                    lat=dest_lat,
                    lng=dest_lng
                )

        elif dest_type == "facility":
            facility = Facility.get(dest_id)
            if not facility:
                raise AppError("Destination facility not found.", code="DESTINATION_NOT_FOUND", status_code=404)
            destination_label = facility.name
            dest_lat = facility.latitude
            dest_lng = facility.longitude
            target_node = cls.pedestrian_service.snap_to_nearest_node(
                campus_id=campus_id,
                lat=facility.latitude,
                lng=facility.longitude
            )

        elif dest_type == "node":
            target_node = NavigationNode.get(dest_id)
            if target_node:
                destination_label = target_node.label or "Campus Point"
                dest_lat = target_node.latitude
                dest_lng = target_node.longitude

        elif "lat" in destination_info and "lng" in destination_info:
            dest_lat = float(destination_info["lat"])
            dest_lng = float(destination_info["lng"])
            target_node = cls.pedestrian_service.snap_to_nearest_node(
                campus_id=campus_id,
                lat=dest_lat,
                lng=dest_lng
            )
            destination_label = "Selected Map Location"

        if not target_node:
            raise AppError("Unable to resolve destination to a walkable campus node.", code="UNRESOLVED_DESTINATION", status_code=400)

        if dest_lat is None:
            dest_lat = target_node.latitude
            dest_lng = target_node.longitude

        # 3. Calculate Multiple Route Candidates
        route_options_spec = [
            {
                "id": "fastest",
                "name": "Fastest Route",
                "badge": "Fastest",
                "mode": "fastest",
                "acc_only": False,
                "description": "Shortest walking path via direct walkways & roads",
            },
            {
                "id": "accessible",
                "name": "Step-Free Accessible",
                "badge": "Step-Free",
                "mode": "accessible",
                "acc_only": True,
                "description": "Smooth ramps & elevators; avoids all stairs",
            },
            {
                "id": "main_avenue",
                "name": "Main Avenue / Shaded",
                "badge": "Wide Boulevard",
                "mode": "main_avenue",
                "acc_only": False,
                "description": "Wide paved central avenues & illuminated plazas",
            },
        ]

        computed_routes = []
        fastest_distance = 0.0

        for spec in route_options_spec:
            try:
                path, total_dist = cls.pedestrian_service.find_optimal_path(
                    campus_id=campus_id,
                    start_node_id=start_node.id,
                    target_node_id=target_node.id,
                    accessible_only=spec["acc_only"],
                    mode=spec["mode"],
                )
            except AppError:
                continue

            orig_extra_dist = haversine_distance(orig_lat, orig_lng, path[0].latitude, path[0].longitude) if (orig_lat is not None and orig_lng is not None) else 0.0
            dest_extra_dist = haversine_distance(dest_lat, dest_lng, path[-1].latitude, path[-1].longitude) if (dest_lat is not None and dest_lng is not None) else 0.0

            geojson_coords = []
            if orig_lat is not None and orig_lng is not None and orig_extra_dist > 1.5:
                geojson_coords.append([round(orig_lng, 6), round(orig_lat, 6)])
            for node in path:
                geojson_coords.append([round(node.longitude, 6), round(node.latitude, 6)])
            if dest_lat is not None and dest_lng is not None and dest_extra_dist > 1.5:
                geojson_coords.append([round(dest_lng, 6), round(dest_lat, 6)])

            # If start_node == target_node and points are distinct
            effective_dist = total_dist
            if start_node.id == target_node.id:
                direct_dist = haversine_distance(orig_lat, orig_lng, dest_lat, dest_lng) if (orig_lat is not None and dest_lat is not None) else 0.0
                effective_dist = direct_dist
                if direct_dist > 3.0:
                    steps = [{
                        "instruction": f"Walk towards {destination_label}",
                        "distance_meters": round(direct_dist, 1),
                        "node_type": "WALKWAY",
                        "floor": start_node.floor
                    }]
                else:
                    steps = [{
                        "instruction": f"You are already at {destination_label}.",
                        "distance_meters": 0,
                        "node_type": "DOOR",
                        "floor": start_node.floor
                    }]
            else:
                effective_dist = total_dist + orig_extra_dist + dest_extra_dist
                steps = cls.pedestrian_service.generate_turn_instructions(path, destination_label)

            walking_time_sec = int(effective_dist / cls.pedestrian_service.AVERAGE_WALKING_SPEED_MPS)
            floor_transitions = sum(1 for s in steps if s.get("node_type") in ["STAIRS", "ELEVATOR"])
            walking_time_sec += floor_transitions * 25

            has_stairs = any(node.node_type == "STAIRS" for node in path)
            is_acc = not has_stairs

            if spec["id"] == "fastest":
                fastest_distance = effective_dist

            computed_routes.append({
                "id": spec["id"],
                "name": spec["name"],
                "badge": spec["badge"],
                "description": spec["description"],
                "mode": spec["mode"],
                "difference": "",
                "total_distance_meters": round(effective_dist, 1),
                "estimated_duration_seconds": max(walking_time_sec, 30),
                "has_stairs": has_stairs,
                "is_accessible": is_acc,
                "geometry": {
                    "type": "LineString",
                    "coordinates": geojson_coords,
                },
                "steps": steps,
            })

        if not computed_routes:
            raise AppError("No connecting walkable path found between origin and destination.", code="ROUTE_NOT_FOUND", status_code=404)

        # Set differences compared to fastest route
        for r in computed_routes:
            if r["id"] == "fastest":
                r["difference"] = "Direct pedestrian route"
            elif r["id"] == "accessible":
                diff = round(r["total_distance_meters"] - fastest_distance)
                if diff > 3:
                    r["difference"] = f"+{diff}m longer • Step-free (0 stairs), ramp accessible"
                else:
                    r["difference"] = "Step-free • Ramp & elevator accessible"
            elif r["id"] == "main_avenue":
                diff = round(r["total_distance_meters"] - fastest_distance)
                if diff > 3:
                    r["difference"] = f"+{diff}m longer • Tree-lined wide avenue"
                else:
                    r["difference"] = "Wide avenue & central plaza promenade"

        # Determine primary selected route
        primary_route = None
        if accessible:
            primary_route = next((r for r in computed_routes if r["id"] == "accessible"), computed_routes[0])
        else:
            primary_route = computed_routes[0]

        return {
            "origin": {
                "node_id": start_node.id,
                "label": start_node.label or "Walkway Point",
                "coordinates": {"latitude": orig_lat or start_node.latitude, "longitude": orig_lng or start_node.longitude}
            },
            "destination": {
                "node_id": target_node.id,
                "label": destination_label,
                "coordinates": {"latitude": dest_lat, "longitude": dest_lng}
            },
            "active_route_id": primary_route["id"],
            "total_distance_meters": primary_route["total_distance_meters"],
            "estimated_duration_seconds": primary_route["estimated_duration_seconds"],
            "accessible": primary_route["is_accessible"],
            "geometry": primary_route["geometry"],
            "steps": primary_route["steps"],
            "routes": computed_routes,
        }

