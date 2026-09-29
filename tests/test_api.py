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


def test_svce_map_search_and_route(client):
    """SVCE JSON data powers campus map, search, and routable coordinates."""
    campuses = client.get("/api/v1/campuses").get_json()["data"]
    assert any(campus["id"] == 2 for campus in campuses)

    map_res = client.get("/api/v1/campuses/2/map-data")
    assert map_res.status_code == 200
    map_data = map_res.get_json()["data"]
    assert map_data["type"] == "FeatureCollection"
    walkways = [feature for feature in map_data["features"] if feature["properties"].get("layer") == "walkway"]
    assert walkways

    search_res = client.get("/api/v1/search?q=Library&campus_id=2")
    assert search_res.status_code == 200
    results = search_res.get_json()["data"]
    assert any("Library" in result["name"] for result in results)
    destination = next(result for result in results if result["type"] == "facility")

    route_res = client.post("/api/v1/routes", json={
        "campus_id": 2,
        "origin": {"lat": 12.9855, "lng": 79.9718},
        "destination": {"type": destination["type"], "id": destination["id"]},
        "accessible": False,
    })
    assert route_res.status_code == 200
    route = route_res.get_json()["data"]["route"]
    coordinates = route["geometry"]["coordinates"]
    assert len(coordinates) >= 2
    assert all(len(point) == 2 and all(isinstance(value, (int, float)) for value in point) for point in coordinates)


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
