"""
Campus Navigation System — Campuses API
Handles campus listings, metadata, and unified GeoJSON map datasets.
"""
from flask import jsonify, g
from app.api.v1 import api_v1_bp
from app.extensions import db
from app.models.campus import Campus
from app.services.location_service import LocationService
from app.utils.errors import AppError


@api_v1_bp.route("/campuses", methods=["GET"])
def get_campuses():
    """List all active campuses."""
    campuses = Campus.query.filter_by(is_active=True).all()
    return jsonify({
        "status": "success",
        "data": [c.to_dict(include_boundary=False) for c in campuses],
        "meta": {"request_id": getattr(g, "request_id", "")}
    }), 200


@api_v1_bp.route("/campuses/<int:campus_id>", methods=["GET"])
def get_campus_detail(campus_id: int):
    """Retrieve detailed metadata and boundary for a specific campus."""
    campus = db.session.get(Campus, campus_id)
    if not campus:
        raise AppError("Campus not found.", code="CAMPUS_NOT_FOUND", status_code=404)

    return jsonify({
        "status": "success",
        "data": campus.to_dict(include_boundary=True),
        "meta": {"request_id": getattr(g, "request_id", "")}
    }), 200


@api_v1_bp.route("/campuses/<int:campus_id>/map-data", methods=["GET"])
def get_campus_map_data(campus_id: int):
    """
    Unified GeoJSON FeatureCollection of all footprints, entrances, facilities,
    and walkways for single-fetch map initialization.
    """
    geojson_data = LocationService.get_campus_geojson(campus_id)
    return jsonify({
        "status": "success",
        "data": geojson_data,
        "meta": {"request_id": getattr(g, "request_id", "")}
    }), 200
