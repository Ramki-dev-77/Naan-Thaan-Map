"""
Campus Navigation System — Routing Engine Test Suite
Tests Haversine mathematics, A* pathfinding, accessibility constraints, and nearest-node snapping.
"""
import heapq
import pytest
from app.services.routing_service import (
    haversine_distance,
    calculate_bearing,
    bearing_to_direction,
    CampusPedestrianRoutingService,
    RoutingService
)
from app.models.campus import Campus
from app.models.room import Room
from app.models.building import Building
from app.models.navigation import NavigationEdge, NavigationNode
from app.utils.errors import AppError


def test_haversine_math():
    """Verify great-circle distance between known coordinates."""
    # Paris to London is approx 343 km (343,000 meters)
    dist = haversine_distance(48.8566, 2.3522, 51.5074, -0.1278)
    assert 340000 < dist < 350000

    # Zero distance between identical points
    assert haversine_distance(12.9716, 77.5946, 12.9716, 77.5946) == 0.0


def test_bearing_directions():
    """Verify cardinal direction conversion."""
    assert bearing_to_direction(0) == "north"
    assert bearing_to_direction(90) == "east"
    assert bearing_to_direction(180) == "south"
    assert bearing_to_direction(270) == "west"


def test_nearest_node_snapping(app_ctx):
    """Verify nearest node resolution on campus."""
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    assert campus is not None

    # Point close to Main Gate (12.9701, 77.5945)
    node = CampusPedestrianRoutingService.snap_to_nearest_node(campus.id, 12.97015, 77.59452)
    assert node is not None
    assert "Main" in (node.label or "") or "Gate" in (node.label or "")


def test_origin_outside_campus_rejected(app_ctx):
    """Verify rejection when coordinates are kilometers away from campus."""
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    # Point ~5 km away
    with pytest.raises(AppError) as exc_info:
        CampusPedestrianRoutingService.snap_to_nearest_node(campus.id, 13.0500, 77.6500, max_radius_meters=300.0)
    assert exc_info.value.code == "ORIGIN_OUTSIDE_CAMPUS"


def test_pathfinding_accessible_vs_stairs(app_ctx):
    """
    Verify that accessible routing strictly navigates around stairs.
    Our seed dataset has a Terrace with stairs (accessible=False) and a Ramp (accessible=True).
    """
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    lower_node = NavigationNode.query.filter_by(campus_id=campus.id, label="Lower Terrace Plaza").first()
    upper_node = NavigationNode.query.filter_by(campus_id=campus.id, label="Upper CS Quad").first()
    assert lower_node is not None
    assert upper_node is not None

    # 1. In standard pedestrian mode, stairs are walkable
    path_standard, dist_std = CampusPedestrianRoutingService.find_optimal_path(
        campus.id, lower_node.id, upper_node.id, accessible_only=False
    )
    assert len(path_standard) >= 2

    # 2. In accessible mode, route MUST NOT include any stairs nodes
    path_acc, dist_acc = CampusPedestrianRoutingService.find_optimal_path(
        campus.id, lower_node.id, upper_node.id, accessible_only=True
    )
    assert len(path_acc) >= 2
    for node in path_acc:
        assert node.node_type != "STAIRS"
    
    # Path with ramp is verified
    node_types = [n.node_type for n in path_acc]
    assert "RAMP" in node_types


def test_full_campus_route_calculation(app_ctx):
    """Verify end-to-end route from Main Gate coordinates to CS-LAB-1."""
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    room = Room.query.filter_by(room_number="CS-LAB-1").first()
    assert room is not None

    origin_coords = {"lat": 12.9701, "lng": 77.5945} # Near Main Gate
    dest_info = {"type": "room", "id": room.id}

    route = RoutingService.calculate_campus_route(campus.id, origin_coords, dest_info, accessible=False)

    assert route["total_distance_meters"] > 0
    assert route["estimated_duration_seconds"] > 0
    assert len(route["geometry"]["coordinates"]) >= 3
    assert len(route["steps"]) >= 2
    assert "Artificial Intelligence" in route["destination"]["label"]
    assert "routes" in route
    assert len(route["routes"]) >= 1


def test_multi_route_options_and_differences(app_ctx):
    """Verify that multiple route alternatives are computed with diff explanations."""
    campus = Campus.query.filter_by(slug="svce-sriperumbudur").first()
    if not campus:
        campus = Campus.query.filter_by(slug="demo-engineering-campus").first()

    room = next((r for r in Room.query.filter_by(room_number="CS-LAB-1").all() if r.building and r.building.campus_id == campus.id), None)
    assert room is not None

    origin_coords = {"lat": campus.latitude - 0.001, "lng": campus.longitude}
    dest_info = {"type": "room", "id": room.id}

    result = RoutingService.calculate_campus_route(campus.id, origin_coords, dest_info, accessible=False)

    assert "routes" in result
    routes = result["routes"]
    assert len(routes) >= 2

    route_ids = [r["id"] for r in routes]
    assert "fastest" in route_ids

    fastest = next(r for r in routes if r["id"] == "fastest")
    assert fastest["total_distance_meters"] > 0
    assert len(fastest["difference"]) > 0

    # If accessible route exists, verify difference exists
    accessible_route = next((r for r in routes if r["id"] == "accessible"), None)
    if accessible_route:
        assert accessible_route["is_accessible"] is True
        assert len(accessible_route["difference"]) > 0


def test_svce_astar_finds_shortest_mixed_walkway_route(app_ctx):
    """A* must not stop at a longer route when discounted path costs are used."""
    campus = Campus.query.filter_by(slug="svce-sriperumbudur").first()
    start = NavigationNode.get(230)
    target = NavigationNode.get(242)
    assert campus is not None
    assert start.campus_id == target.campus_id == campus.id

    edges = [
        edge for edge in NavigationEdge.query.all()
        if edge.source_node and edge.source_node.campus_id == campus.id
        and edge.destination_node and edge.destination_node.is_active
    ]

    def edge_cost(edge):
        if edge.stairs:
            return edge.distance * 12.0
        if edge.path_type == "MAIN_AVENUE":
            return edge.distance * 0.65
        if edge.path_type == "PAVED_WALKWAY":
            return edge.distance * 0.95
        return edge.distance * 2.2

    distances = {start.id: 0.0}
    queue = [(0.0, start.id)]
    while queue:
        cost, node_id = heapq.heappop(queue)
        if cost != distances[node_id]:
            continue
        if node_id == target.id:
            break
        for edge in edges:
            if edge.source_node_id == node_id:
                neighbor_id = edge.destination_node_id
            elif edge.is_bidirectional and edge.destination_node_id == node_id:
                neighbor_id = edge.source_node_id
            else:
                continue
            candidate = cost + edge_cost(edge)
            if candidate < distances.get(neighbor_id, float("inf")):
                distances[neighbor_id] = candidate
                heapq.heappush(queue, (candidate, neighbor_id))

    path, _ = CampusPedestrianRoutingService.find_optimal_path(
        campus.id, start.id, target.id, mode="main_avenue"
    )
    actual_cost = sum(
        min(
            edge_cost(edge) for edge in edges
            if (edge.source_node_id == source.id and edge.destination_node_id == destination.id)
            or (edge.is_bidirectional and edge.source_node_id == destination.id and edge.destination_node_id == source.id)
        )
        for source, destination in zip(path, path[1:])
    )

    assert actual_cost == pytest.approx(distances[target.id], abs=0.01)


def test_svce_shortest_routes_use_all_walkable_edge_types(app_ctx):
    """SVCE routes traverse connected road and pedestrian edges with network geometry."""
    campus = Campus.query.filter_by(slug="svce-sriperumbudur").first()
    nodes = {node.id: node for node in NavigationNode.query.filter_by(campus_id=campus.id, is_active=True).all()}
    edges = [
        edge for edge in NavigationEdge.query.all()
        if edge.source_node and edge.source_node.campus_id == campus.id
        and edge.destination_node and edge.destination_node.is_active
    ]
    node_ids = set(nodes)
    assert edges
    assert all(
        edge.source_node_id in node_ids and edge.destination_node_id in node_ids and edge.distance > 0
        for edge in edges
    )
    assert {edge.path_type for edge in edges} >= {"MAIN_AVENUE", "PAVED_WALKWAY"}

    adjacency = {node_id: set() for node_id in node_ids}
    for edge in edges:
        adjacency[edge.source_node_id].add(edge.destination_node_id)
        if edge.is_bidirectional:
            adjacency[edge.destination_node_id].add(edge.source_node_id)
    reachable = set()
    pending = [next(iter(node_ids))]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(adjacency[node_id] - reachable)
    assert reachable == node_ids

    def shortest_distance(start_id, target_id, allowed_types=None):
        distances = {start_id: 0.0}
        queue = [(0.0, start_id)]
        while queue:
            cost, node_id = heapq.heappop(queue)
            if cost != distances[node_id]:
                continue
            if node_id == target_id:
                return cost
            for edge in edges:
                if allowed_types and edge.path_type not in allowed_types:
                    continue
                if edge.source_node_id == node_id:
                    neighbor_id = edge.destination_node_id
                elif edge.is_bidirectional and edge.destination_node_id == node_id:
                    neighbor_id = edge.source_node_id
                else:
                    continue
                candidate = cost + edge.distance
                if candidate < distances.get(neighbor_id, float("inf")):
                    distances[neighbor_id] = candidate
                    heapq.heappush(queue, (candidate, neighbor_id))
        return float("inf")

    def selected_edges(path):
        return [
            next(
                edge for edge in edges
                if (edge.source_node_id == source.id and edge.destination_node_id == destination.id)
                or (edge.is_bidirectional and edge.source_node_id == destination.id and edge.destination_node_id == source.id)
            )
            for source, destination in zip(path, path[1:])
        ]

    road_start, road_end = nodes[209], nodes[155]
    road_path, _ = CampusPedestrianRoutingService.find_optimal_path(
        campus.id, road_start.id, road_end.id, mode="fastest"
    )
    assert [node.id for node in road_path] == [road_start.id, road_end.id]
    assert selected_edges(road_path)[0].path_type == "MAIN_AVENUE"

    mixed_path, mixed_distance = CampusPedestrianRoutingService.find_optimal_path(
        campus.id, 175, 215, mode="fastest"
    )
    mixed_types = {edge.path_type for edge in selected_edges(mixed_path)}
    assert {"MAIN_AVENUE", "PAVED_WALKWAY"}.issubset(mixed_types)
    assert mixed_distance == pytest.approx(shortest_distance(175, 215), abs=0.01)

    walkway_path, _ = CampusPedestrianRoutingService.find_optimal_path(
        campus.id, 148, 149, mode="fastest"
    )
    assert [edge.path_type for edge in selected_edges(walkway_path)] == ["PAVED_WALKWAY"]
    walkway_node = nodes[148]
    assert CampusPedestrianRoutingService.snap_to_nearest_node(
        campus.id, walkway_node.latitude, walkway_node.longitude
    ).id == walkway_node.id

    building_start, building_end = nodes[230], nodes[242]
    assert building_start.node_type == building_end.node_type == "ENTRANCE"
    assert building_start.building_id != building_end.building_id
    building_path, _ = CampusPedestrianRoutingService.find_optimal_path(
        campus.id, building_start.id, building_end.id, mode="fastest"
    )
    assert "PAVED_WALKWAY" in {edge.path_type for edge in selected_edges(building_path)}

    all_edge_distance = shortest_distance(210, 106)
    road_only_distance = shortest_distance(210, 106, {"MAIN_AVENUE"})
    assert all_edge_distance == pytest.approx(408.3, abs=0.1)
    assert road_only_distance == pytest.approx(742.1, abs=0.1)
    assert all_edge_distance < road_only_distance

    route = RoutingService.calculate_campus_route(
        campus.id,
        {"lat": nodes[210].latitude, "lng": nodes[210].longitude},
        {"type": "node", "id": 106},
        accessible=False,
    )
    expected_coordinates = [
        [round(node.longitude, 6), round(node.latitude, 6)]
        for node in CampusPedestrianRoutingService.find_optimal_path(
            campus.id, 210, 106, mode="fastest"
        )[0]
    ]
    assert route["geometry"]["coordinates"] == expected_coordinates
    assert all(-180 <= longitude <= 180 and -90 <= latitude <= 90 for longitude, latitude in expected_coordinates)

