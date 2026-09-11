"""
Campus Navigation System — API v1 Blueprint
Aggregates versioned REST endpoints.
"""
from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__)

from app.api.v1 import campuses, search, routes, locations, facilities, admin
