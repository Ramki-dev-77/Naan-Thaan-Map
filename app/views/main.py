"""
Campus Navigation System — Main Public View
Renders the primary single-page campus map, search interface, and navigation drawer.
"""
from flask import Blueprint, render_template, current_app
from app.models.campus import Campus
from app.models.category import Category

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index():
    """Main interactive map and navigation view."""
    campuses = Campus.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    default_campus = campuses[0] if campuses else None

    return render_template(
        "index.html",
        campuses=campuses,
        categories=categories,
        default_campus=default_campus,
        google_maps_key=current_app.config.get("GOOGLE_MAPS_API_KEY", "")
    )
