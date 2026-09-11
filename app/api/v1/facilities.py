"""
Campus Navigation System — Facilities API
Serves campus points of interest, parking lots, medical centers, and amenities.
"""
from flask import request, jsonify, g
from app.api.v1 import api_v1_bp
from app.models.facility import Facility


@api_v1_bp.route("/facilities", methods=["GET"])
def get_facilities():
    """
    List campus facilities.
    Query parameters:
    - campus_id: Optional campus ID
    - category_id: Optional category ID
    """
    campus_id = request.args.get("campus_id", type=int)
    category_id = request.args.get("category_id", type=int)

    query = Facility.query
    if campus_id:
        query = query.filter(Facility.campus_id == campus_id)
    if category_id:
        query = query.filter(Facility.category_id == category_id)

    facilities = query.all()
    return jsonify({
        "status": "success",
        "data": [f.to_dict() for f in facilities],
        "meta": {
            "count": len(facilities),
            "request_id": getattr(g, "request_id", "")
        }
    }), 200
