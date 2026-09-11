"""
Campus Navigation System — Validation Service
Validates geographic coordinates, geometries, route requests, and admin payloads.
"""
from typing import Dict, Any, Tuple
from app.utils.errors import AppError


class ValidationService:
    @staticmethod
    def validate_coordinates(lat: Any, lng: Any, field_name: str = "Coordinates") -> Tuple[float, float]:
        """Validate latitude in [-90, 90] and longitude in [-180, 180]."""
        try:
            latitude = float(lat)
            longitude = float(lng)
        except (ValueError, TypeError):
            raise AppError(
                f"{field_name} must contain valid floating-point numbers.",
                code="INVALID_COORDINATES",
                status_code=400,
            )

        if not (-90.0 <= latitude <= 90.0):
            raise AppError(
                f"Latitude {latitude} is outside the valid range [-90.0, 90.0].",
                code="INVALID_LATITUDE",
                status_code=400,
            )

        if not (-180.0 <= longitude <= 180.0):
            raise AppError(
                f"Longitude {longitude} is outside the valid range [-180.0, 180.0].",
                code="INVALID_LONGITUDE",
                status_code=400,
            )

        return latitude, longitude

    @classmethod
    def validate_route_request(cls, payload: Dict[str, Any]) -> Tuple[int, Dict[str, float], Dict[str, Any], bool]:
        """Validate payload for POST /api/v1/routes."""
        if not payload or not isinstance(payload, dict):
            raise AppError("Request body must be a valid JSON object.", code="INVALID_JSON", status_code=400)

        campus_id = payload.get("campus_id")
        if not campus_id:
            raise AppError("campus_id is required.", code="MISSING_CAMPUS_ID", status_code=400)

        origin = payload.get("origin")
        if not origin or not isinstance(origin, dict):
            raise AppError("origin must be an object containing 'lat' and 'lng'.", code="INVALID_ORIGIN", status_code=400)

        orig_lat, orig_lng = cls.validate_coordinates(origin.get("lat"), origin.get("lng"), "Origin")

        destination = payload.get("destination")
        if not destination or not isinstance(destination, dict):
            raise AppError("destination must be an object with destination target information.", code="INVALID_DESTINATION", status_code=400)

        accessible = bool(payload.get("accessible", False))

        return campus_id, {"lat": orig_lat, "lng": orig_lng}, destination, accessible
