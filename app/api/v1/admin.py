"""
Campus Navigation System — Admin API
Authenticated REST management endpoints for campus geometry, buildings, rooms,
facilities, network nodes, and audit logs.
Zero-database implementation using in-memory data store.
"""
import json
from flask import request, jsonify, session, g
from app.api.v1 import api_v1_bp
from app.extensions import limiter
from app.data_store import data_store
from app.models.admin import AdminUser
from app.models.audit import AuditLog
from app.models.building import Building
from app.models.room import Room
from app.models.facility import Facility
from app.models.navigation import NavigationNode, NavigationEdge
from app.utils.security import verify_password, login_admin, logout_admin, admin_required
from app.utils.errors import AppError


def log_audit_action(action: str, entity_type: str, entity_id: int = None, metadata: dict = None):
    """Utility to record administrative action in in-memory AuditLog."""
    admin_id = session.get("admin_id")
    remote_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    log_entry = AuditLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata) if metadata else None,
        ip_address=remote_ip,
    )
    data_store.add(log_entry)


@api_v1_bp.route("/admin/login", methods=["POST"])
@limiter.limit("10 per minute")
def admin_api_login():
    """Admin login endpoint."""
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "")

    if not username or not password:
        raise AppError("Username and password are required.", code="MISSING_CREDENTIALS", status_code=400)

    admin = AdminUser.query.filter_by(username=username, is_active=True).first()
    if not admin or not verify_password(password, admin.password_hash):
        raise AppError("Invalid username or password.", code="INVALID_CREDENTIALS", status_code=401)

    login_admin({"id": admin.id, "username": admin.username, "role": admin.role})
    log_audit_action("ADMIN_LOGIN", "AdminUser", admin.id, {"username": admin.username})

    return jsonify({
        "status": "success",
        "data": {
            "user": admin.to_dict(),
            "message": "Authentication successful"
        }
    }), 200


@api_v1_bp.route("/admin/logout", methods=["POST"])
@admin_required
def admin_api_logout():
    """Admin logout endpoint."""
    admin_id = session.get("admin_id")
    log_audit_action("ADMIN_LOGOUT", "AdminUser", admin_id)
    logout_admin()
    return jsonify({"status": "success", "message": "Logged out successfully"}), 200


# --- Buildings CRUD ---

@api_v1_bp.route("/admin/buildings", methods=["POST"])
@admin_required
def create_building():
    payload = request.get_json(silent=True) or {}
    campus_id = payload.get("campus_id")
    name = payload.get("name")
    code = payload.get("code")
    lat = payload.get("latitude")
    lng = payload.get("longitude")

    if not all([campus_id, name, code, lat is not None, lng is not None]):
        raise AppError("campus_id, name, code, latitude, and longitude are required.", code="INVALID_PAYLOAD", status_code=400)

    building = Building(
        campus_id=campus_id,
        name=name,
        code=code,
        description=payload.get("description"),
        latitude=float(lat),
        longitude=float(lng),
        entrance_latitude=float(payload.get("entrance_latitude", lat)),
        entrance_longitude=float(payload.get("entrance_longitude", lng)),
        footprint=payload.get("footprint"),
        floors=int(payload.get("floors", 1)),
        accessible=bool(payload.get("accessible", True))
    )
    data_store.add(building)
    log_audit_action("CREATE_BUILDING", "Building", building.id, {"name": name, "code": code})
    return jsonify({"status": "success", "data": building.to_dict()}), 201


@api_v1_bp.route("/admin/buildings/<int:building_id>", methods=["PUT"])
@admin_required
def update_building(building_id: int):
    building = Building.get(building_id)
    if not building:
        raise AppError("Building not found.", code="BUILDING_NOT_FOUND", status_code=404)

    payload = request.get_json(silent=True) or {}
    if "name" in payload:
        building.name = payload["name"]
    if "code" in payload:
        building.code = payload["code"]
    if "description" in payload:
        building.description = payload["description"]
    if "latitude" in payload and "longitude" in payload:
        building.latitude = float(payload["latitude"])
        building.longitude = float(payload["longitude"])
    if "entrance_latitude" in payload and "entrance_longitude" in payload:
        building.entrance_latitude = float(payload["entrance_latitude"])
        building.entrance_longitude = float(payload["entrance_longitude"])
    if "footprint" in payload:
        building.footprint = payload["footprint"]
    if "floors" in payload:
        building.floors = int(payload["floors"])
    if "accessible" in payload:
        building.accessible = bool(payload["accessible"])

    data_store.add(building)
    log_audit_action("UPDATE_BUILDING", "Building", building.id, {"updated_fields": list(payload.keys())})
    return jsonify({"status": "success", "data": building.to_dict()}), 200


@api_v1_bp.route("/admin/buildings/<int:building_id>", methods=["DELETE"])
@admin_required
def delete_building(building_id: int):
    building = Building.get(building_id)
    if not building:
        raise AppError("Building not found.", code="BUILDING_NOT_FOUND", status_code=404)

    b_name = building.name
    data_store.delete(building)
    log_audit_action("DELETE_BUILDING", "Building", building_id, {"name": b_name})
    return jsonify({"status": "success", "message": f"Building {b_name} deleted."}), 200


# --- Rooms CRUD ---

@api_v1_bp.route("/admin/rooms", methods=["POST"])
@admin_required
def create_room():
    payload = request.get_json(silent=True) or {}
    building_id = payload.get("building_id")
    room_number = payload.get("room_number")
    name = payload.get("name")

    if not all([building_id, room_number, name]):
        raise AppError("building_id, room_number, and name are required.", code="INVALID_PAYLOAD", status_code=400)

    room = Room(
        building_id=building_id,
        room_number=room_number,
        name=name,
        floor=int(payload.get("floor", 0)),
        department=payload.get("department"),
        description=payload.get("description"),
        latitude=float(payload["latitude"]) if "latitude" in payload and payload["latitude"] is not None else None,
        longitude=float(payload["longitude"]) if "longitude" in payload and payload["longitude"] is not None else None,
        node_id=payload.get("node_id")
    )
    data_store.add(room)
    log_audit_action("CREATE_ROOM", "Room", room.id, {"room_number": room_number, "name": name})
    return jsonify({"status": "success", "data": room.to_dict()}), 201


# --- Facilities CRUD ---

@api_v1_bp.route("/admin/facilities", methods=["POST"])
@admin_required
def create_facility():
    payload = request.get_json(silent=True) or {}
    campus_id = payload.get("campus_id")
    category_id = payload.get("category_id")
    name = payload.get("name")
    lat = payload.get("latitude")
    lng = payload.get("longitude")

    if not all([campus_id, category_id, name, lat is not None, lng is not None]):
        raise AppError("campus_id, category_id, name, latitude, and longitude are required.", code="INVALID_PAYLOAD", status_code=400)

    facility = Facility(
        campus_id=campus_id,
        building_id=payload.get("building_id"),
        category_id=category_id,
        name=name,
        description=payload.get("description"),
        latitude=float(lat),
        longitude=float(lng),
        accessible=bool(payload.get("accessible", True)),
        opening_hours=payload.get("opening_hours")
    )
    data_store.add(facility)
    log_audit_action("CREATE_FACILITY", "Facility", facility.id, {"name": name})
    return jsonify({"status": "success", "data": facility.to_dict()}), 201


# --- Navigation Graph Editor (Nodes & Edges) ---

@api_v1_bp.route("/admin/nodes", methods=["POST"])
@admin_required
def create_node():
    payload = request.get_json(silent=True) or {}
    campus_id = payload.get("campus_id")
    lat = payload.get("latitude")
    lng = payload.get("longitude")

    if not all([campus_id, lat is not None, lng is not None]):
        raise AppError("campus_id, latitude, and longitude are required.", code="INVALID_PAYLOAD", status_code=400)

    node = NavigationNode(
        campus_id=campus_id,
        building_id=payload.get("building_id"),
        node_type=payload.get("node_type", "JUNCTION"),
        label=payload.get("label"),
        floor=int(payload.get("floor", 0)),
        latitude=float(lat),
        longitude=float(lng),
        is_active=bool(payload.get("is_active", True))
    )
    data_store.add(node)
    log_audit_action("CREATE_NODE", "NavigationNode", node.id, {"label": node.label, "type": node.node_type})
    return jsonify({"status": "success", "data": node.to_dict()}), 201


@api_v1_bp.route("/admin/edges", methods=["POST"])
@admin_required
def create_edge():
    payload = request.get_json(silent=True) or {}
    src_id = payload.get("source_node_id")
    dst_id = payload.get("destination_node_id")
    distance = payload.get("distance")

    if not all([src_id, dst_id, distance is not None]):
        raise AppError("source_node_id, destination_node_id, and distance are required.", code="INVALID_PAYLOAD", status_code=400)

    edge = NavigationEdge(
        source_node_id=src_id,
        destination_node_id=dst_id,
        distance=float(distance),
        accessible=bool(payload.get("accessible", True)),
        stairs=bool(payload.get("stairs", False)),
        path_type=payload.get("path_type", "PAVED_WALKWAY"),
        is_bidirectional=bool(payload.get("is_bidirectional", True))
    )
    data_store.add(edge)
    log_audit_action("CREATE_EDGE", "NavigationEdge", edge.id, {"src": src_id, "dst": dst_id})
    return jsonify({"status": "success", "data": edge.to_dict()}), 201


# --- Audit Logs ---

@api_v1_bp.route("/admin/audit-logs", methods=["GET"])
@admin_required
def get_audit_logs():
    limit = request.args.get("limit", 50, type=int)
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(min(limit, 100)).all()
    return jsonify({
        "status": "success",
        "data": [l.to_dict() for l in logs],
        "meta": {"count": len(logs)}
    }), 200
