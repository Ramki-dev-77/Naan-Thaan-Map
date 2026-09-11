"""
Campus Navigation System — Routing Engine Test Suite
Tests Haversine mathematics, A* pathfinding, accessibility constraints, and nearest-node snapping.
"""
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
from app.models.navigation import NavigationNode
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
