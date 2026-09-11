"""
Campus Navigation System — Routing API
Calculates pedestrian routes over the verified campus walkway graph.
"""
from flask import request, jsonify, g
from app.api.v1 import api_v1_bp
from app.extensions import limiter
from app.services.routing_service import RoutingService
from app.services.validation_service import ValidationService


@api_v1_bp.route("/routes", methods=["POST"])
@limiter.limit("40 per minute")
def calculate_route():
    """
    Compute walking route between origin coordinates and campus destination.
    Payload:
    {
      "campus_id": 1,
      "origin": { "lat": 12.9716, "lng": 77.5946 },
      "destination": { "type": "room", "id": 5 },
      "accessible": false
    }
    """
    payload = request.get_json(silent=True) or {}
    campus_id, origin_coords, destination_info, accessible = ValidationService.validate_route_request(payload)

    route_data = RoutingService.calculate_campus_route(
        campus_id=campus_id,
        origin_coords=origin_coords,
        destination_info=destination_info,
        accessible=accessible
    )

    return jsonify({
        "status": "success",
        "data": {
            "route": route_data
        },
        "meta": {"request_id": getattr(g, "request_id", "")}
    }), 200
