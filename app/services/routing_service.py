"""
Campus Navigation System — Routing Engine
Implements the Campus Pedestrian Graph and A* Pathfinding Algorithm with
accessibility constraints, nearest-node snapping, and turn-by-turn instruction generation.
"""
import math
import heapq
from typing import List, Dict, Tuple, Optional, Any
from app.extensions import db
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
    def snap_to_nearest_node(cls, campus_id: int, lat: float, lng: float, max_radius_meters: float = 300.0) -> NavigationNode:
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
    def find_optimal_path(cls, campus_id: int, start_node_id: int, target_node_id: int, accessible_only: bool = False) -> Tuple[List[NavigationNode], float]:
        """
        Executes A* search from start_node_id to target_node_id.
        Returns (node_sequence, total_distance_meters).
        """
        if start_node_id == target_node_id:
            node = db.session.get(NavigationNode, start_node_id)
            return ([node] if node else []), 0.0

        # Load all active nodes and edges for this campus
        nodes_dict = {n.id: n for n in NavigationNode.query.filter_by(campus_id=campus_id, is_active=True).all()}
        if start_node_id not in nodes_dict or target_node_id not in nodes_dict:
            raise AppError("Start or target navigation node is not active or recognized.", code="NODE_NOT_FOUND", status_code=404)

        target_node = nodes_dict[target_node_id]

        # Build adjacency graph
        edges = NavigationEdge.query.join(NavigationNode, NavigationEdge.source_node_id == NavigationNode.id)\
            .filter(NavigationNode.campus_id == campus_id).all()

        adj: Dict[int, List[Tuple[int, float, bool, bool, str]]] = {nid: [] for nid in nodes_dict}

        for edge in edges:
            if edge.source_node_id in adj and edge.destination_node_id in nodes_dict:
                # If accessible routing is requested, discard stairs completely
                if accessible_only and (edge.stairs or not edge.accessible):
                    continue
                
                # Weight calculation: stairs penalty if not in accessible mode
                weight = edge.distance
                if edge.stairs:
                    weight *= 1.8  # Pedestrian reluctance to climb stairs

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
                return path, g_scores[target_node_id]

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
        if accessible_only:
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
        Coordinates origin snapping, target node identification, A* pathfinding,
        and response formatting.
        """
        # 1. Snap origin to closest campus node
        start_node = cls.pedestrian_service.snap_to_nearest_node(
            campus_id=campus_id,
            lat=origin_coords["lat"],
            lng=origin_coords["lng"]
        )

        # 2. Resolve target node
        dest_type = destination_info.get("type")
        dest_id = destination_info.get("id")
        target_node = None
        destination_label = "Destination"

        if dest_type == "room":
            room = db.session.get(Room, dest_id)
            if not room:
                raise AppError("Destination room not found.", code="DESTINATION_NOT_FOUND", status_code=404)
            destination_label = f"{room.room_number} — {room.name}"
            # If room has specific door node, use it; otherwise use building entrance
            if room.node_id:
                target_node = db.session.get(NavigationNode, room.node_id)
            if not target_node and room.building:
                target_node = NavigationNode.query.filter_by(building_id=room.building_id, node_type="ENTRANCE").first()
                if not target_node:
                    target_node = cls.pedestrian_service.snap_to_nearest_node(
                        campus_id=campus_id,
                        lat=room.building.entrance_latitude or room.building.latitude,
                        lng=room.building.entrance_longitude or room.building.longitude
                    )

        elif dest_type == "building":
            building = db.session.get(Building, dest_id)
            if not building:
                raise AppError("Destination building not found.", code="DESTINATION_NOT_FOUND", status_code=404)
            destination_label = building.name
            target_node = NavigationNode.query.filter_by(building_id=building.id, node_type="ENTRANCE").first()
            if not target_node:
                target_node = cls.pedestrian_service.snap_to_nearest_node(
                    campus_id=campus_id,
                    lat=building.entrance_latitude or building.latitude,
                    lng=building.entrance_longitude or building.longitude
                )

        elif dest_type == "facility":
            facility = db.session.get(Facility, dest_id)
            if not facility:
                raise AppError("Destination facility not found.", code="DESTINATION_NOT_FOUND", status_code=404)
            destination_label = facility.name
            target_node = cls.pedestrian_service.snap_to_nearest_node(
                campus_id=campus_id,
                lat=facility.latitude,
                lng=facility.longitude
            )

        elif dest_type == "node":
            target_node = db.session.get(NavigationNode, dest_id)
            if target_node:
                destination_label = target_node.label or "Campus Point"

        elif "lat" in destination_info and "lng" in destination_info:
            target_node = cls.pedestrian_service.snap_to_nearest_node(
                campus_id=campus_id,
                lat=destination_info["lat"],
                lng=destination_info["lng"]
            )
            destination_label = "Selected Map Location"

        if not target_node:
            raise AppError("Unable to resolve destination to a walkable campus node.", code="UNRESOLVED_DESTINATION", status_code=400)

        # 3. Compute A* Path
        path, total_distance = cls.pedestrian_service.find_optimal_path(
            campus_id=campus_id,
            start_node_id=start_node.id,
            target_node_id=target_node.id,
            accessible_only=accessible
        )

        # 4. Generate GeoJSON coordinates [[lng, lat], ...]
        geojson_coords = [[node.longitude, node.latitude] for node in path]

        # 5. Turn-by-turn guidance
        steps = cls.pedestrian_service.generate_turn_instructions(path, destination_label)

        # 6. Estimate walking duration (seconds)
        walking_time_sec = int(total_distance / cls.pedestrian_service.AVERAGE_WALKING_SPEED_MPS)
        # Add buffer for floor transitions (e.g. elevator/stairs)
        floor_transitions = sum(1 for s in steps if s["node_type"] in ["STAIRS", "ELEVATOR"])
        walking_time_sec += floor_transitions * 25

        return {
            "origin": {
                "node_id": start_node.id,
                "label": start_node.label or "Walkway Point",
                "coordinates": {"latitude": start_node.latitude, "longitude": start_node.longitude}
            },
            "destination": {
                "node_id": target_node.id,
                "label": destination_label,
                "coordinates": {"latitude": target_node.latitude, "longitude": target_node.longitude}
            },
            "total_distance_meters": round(total_distance, 1),
            "estimated_duration_seconds": max(walking_time_sec, 30),
            "accessible": accessible,
            "geometry": {
                "type": "LineString",
                "coordinates": geojson_coords,
            },
            "steps": steps,
        }
