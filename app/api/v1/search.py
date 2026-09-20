"""
Campus Navigation System — Search API
Provides multi-attribute search across rooms, buildings, labs, and facilities with ranking.
"""
from flask import request, jsonify, g
from app.api.v1 import api_v1_bp
from app.extensions import limiter
from app.services.search_service import SearchService


@api_v1_bp.route("/search", methods=["GET"])
@limiter.limit("60 per minute")
def search():
    """
    Search campus entities.
    Query parameters:
    - q: Search string (e.g. "CS Lab", "Room 204", "Library")
    - campus_id: Optional campus filter
    - category: Optional category slug filter
    - limit: Max results (default 15)
    """
    query_str = request.args.get("q", "").strip()
    campus_id = request.args.get("campus_id", type=int)
    category_slug = request.args.get("category", "").strip() or None
    limit = request.args.get("limit", 30, type=int)

    if not query_str and not category_slug:
        return jsonify({
            "status": "success",
            "data": [],
            "meta": {"query": "", "count": 0, "request_id": getattr(g, "request_id", "")}
        }), 200

    results = SearchService.search(
        query=query_str or "*",
        campus_id=campus_id,
        category_slug=category_slug,
        limit=min(limit, 100)
    )

    return jsonify({
        "status": "success",
        "data": results,
        "meta": {
            "query": query_str,
            "count": len(results),
            "request_id": getattr(g, "request_id", "")
        }
    }), 200
