"""
Campus Navigation System — API Integration Tests
Validates REST endpoints, GeoJSON outputs, and error response envelopes.
"""
import json


def test_health_probe(client):
    """GET /health must return 200 with status 'ok'."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"


def test_readiness_probe(client):
    """GET /ready must return 200 when database is healthy."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ready"


def test_get_campuses(client):
    """GET /api/v1/campuses must return active campuses."""
    res = client.get("/api/v1/campuses")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["data"]) >= 1


def test_get_campus_map_data(client):
    """GET /api/v1/campuses/1/map-data must return valid GeoJSON FeatureCollection."""
    res = client.get("/api/v1/campuses/1/map-data")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    geojson = data["data"]
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0

    layers = {f["properties"].get("layer") for f in geojson["features"]}
    assert "building_footprint" in layers
    assert "facility" in layers
    assert "walkway" in layers


def test_search_api(client):
    """GET /api/v1/search returns ranked results."""
    res = client.get("/api/v1/search?q=Library&campus_id=1")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["data"]) > 0


def test_routes_api_success(client):
    """POST /api/v1/routes creates route between gate and library."""
    payload = {
        "campus_id": 1,
        "origin": {"lat": 12.9701, "lng": 77.5945},
        "destination": {"type": "facility", "id": 1},
        "accessible": False
    }
    res = client.post("/api/v1/routes", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    route = data["data"]["route"]
    assert route["total_distance_meters"] >= 0
    assert "geometry" in route


def test_routes_api_invalid_coords(client):
    """POST /api/v1/routes returns standard error envelope on invalid coordinates."""
    payload = {
        "campus_id": 1,
        "origin": {"lat": 95.0, "lng": 77.5945}, # 95.0 is invalid latitude
        "destination": {"type": "facility", "id": 1}
    }
    res = client.post("/api/v1/routes", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "INVALID_LATITUDE"
    assert "meta" in data
    assert "timestamp" in data["meta"]
