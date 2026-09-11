"""
Campus Navigation System — Search Service Test Suite
Tests exact matching, room number matching, fuzzy search, ranking, and category filters.
"""
from app.services.search_service import SearchService
from app.models.campus import Campus


def test_search_exact_building_code(app_ctx):
    """Searching building code 'CSB' should rank Computer Science Block at top with high score."""
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    results = SearchService.search("CSB", campus_id=campus.id)
    assert len(results) > 0
    top = results[0]
    assert top["type"] == "building"
    assert "Computer Science" in top["name"]
    assert top["relevance"] >= 0.95


def test_search_room_number(app_ctx):
    """Searching room number 'CS-101' should return the exact room."""
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    results = SearchService.search("CS-101", campus_id=campus.id)
    assert len(results) > 0
    assert any("CS-101" in r["name"] for r in results)


def test_search_fuzzy_query(app_ctx):
    """Searching for 'Robotics' should locate AI & Robotics Lab."""
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    results = SearchService.search("Robotics", campus_id=campus.id)
    assert len(results) > 0
    names = [r["name"] for r in results]
    assert any("Robotics" in n for n in names)


def test_search_category_filter(app_ctx):
    """Filtering by category 'dining' should only return dining facilities."""
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    results = SearchService.search("Cafeteria", campus_id=campus.id, category_slug="dining")
    assert len(results) > 0
    for r in results:
        assert r["category"].lower() == "dining"
