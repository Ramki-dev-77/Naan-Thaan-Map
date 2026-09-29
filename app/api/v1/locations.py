"""
Campus Navigation System — Locations API
Serves specific Building, Room, and Category records.
Zero-database implementation reading from in-memory data store.
"""
from flask import jsonify, g
from app.api.v1 import api_v1_bp
from app.models.building import Building
from app.models.room import Room
from app.models.category import Category
from app.utils.errors import AppError


@api_v1_bp.route("/buildings/<int:building_id>", methods=["GET"])
def get_building(building_id: int):
    """Retrieve detailed metadata and rooms for a building."""
    building = Building.get(building_id)
    if not building:
        raise AppError("Building not found.", code="BUILDING_NOT_FOUND", status_code=404)

    return jsonify({
        "status": "success",
        "data": building.to_dict(include_rooms=True),
        "meta": {"request_id": getattr(g, "request_id", "")}
    }), 200


@api_v1_bp.route("/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id: int):
    """Retrieve details for a specific room or lab."""
    room = Room.get(room_id)
    if not room:
        raise AppError("Room not found.", code="ROOM_NOT_FOUND", status_code=404)

    return jsonify({
        "status": "success",
        "data": room.to_dict(),
        "meta": {"request_id": getattr(g, "request_id", "")}
    }), 200


@api_v1_bp.route("/categories", methods=["GET"])
def get_categories():
    """List all taxonomy categories with colors and icons."""
    categories = Category.query.all()
    return jsonify({
        "status": "success",
        "data": [c.to_dict() for c in categories],
        "meta": {"request_id": getattr(g, "request_id", "")}
    }), 200
