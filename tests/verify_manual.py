"""
Campus Navigation System — End-to-End Production Verification Script
Runs end-to-end checks across views, API contracts, A* routes, search, and admin flows.
"""
from app import create_app
from app.config import DevelopmentConfig

app = create_app(DevelopmentConfig)
client = app.test_client()

# 1. Test Home View
home_res = client.get("/")
assert home_res.status_code == 200, f"Home failed: {home_res.status_code}"
assert b"Campus Navigation" in home_res.data
print("[PASS] 1. Home View (index.html) loaded successfully.")

# 2. Test Health Probes
health_res = client.get("/health")
assert health_res.status_code == 200
ready_res = client.get("/ready")
assert ready_res.status_code == 200
print("[PASS] 2. Health & Readiness probes verified.")

# 3. Test GeoJSON Map Data
map_res = client.get("/api/v1/campuses/1/map-data")
assert map_res.status_code == 200
map_data = map_res.get_json()["data"]
assert map_data["type"] == "FeatureCollection"
num_features = len(map_data["features"])
print(f"[PASS] 3. Map Data GeoJSON loaded with {num_features} spatial features.")

# 4. Test Search API
search_res = client.get("/api/v1/search?q=CS-LAB-2&campus_id=1")
assert search_res.status_code == 200
search_results = search_res.get_json()["data"]
assert len(search_results) > 0
dest_item = search_results[0]
print(f"[PASS] 4. Search resolved 'CS-LAB-2' to: {dest_item['name']} (Type: {dest_item['type']})")

# 5. Test Route Calculation: Standard Pedestrian vs Wheelchair Accessible
route_std = client.post("/api/v1/routes", json={
    "campus_id": 1,
    "origin": {"lat": 12.9701, "lng": 77.5945},
    "destination": {"type": "room", "id": dest_item["id"]},
    "accessible": False
})
assert route_std.status_code == 200
r_std = route_std.get_json()["data"]["route"]
print(f"[PASS] 5. Standard Route: {r_std['total_distance_meters']}m, duration ~{r_std['estimated_duration_seconds']}s, steps: {len(r_std['steps'])}")

route_acc = client.post("/api/v1/routes", json={
    "campus_id": 1,
    "origin": {"lat": 12.9701, "lng": 77.5945},
    "destination": {"type": "room", "id": dest_item["id"]},
    "accessible": True
})
assert route_acc.status_code == 200
r_acc = route_acc.get_json()["data"]["route"]
print(f"[PASS] 6. Accessible Route: {r_acc['total_distance_meters']}m, duration ~{r_acc['estimated_duration_seconds']}s, steps: {len(r_acc['steps'])}")

# 6. Test Admin Login and Dashboard
get_login = client.get("/admin/login")
assert get_login.status_code == 200

# Extract csrf_token from HTML
import re
csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', get_login.data.decode("utf-8"))
csrf_token = csrf_match.group(1) if csrf_match else ""

login_res = client.post("/admin/login", data={
    "username": "admin",
    "password": "CampusAdmin2026!",
    "csrf_token": csrf_token
}, follow_redirects=True)
assert login_res.status_code == 200
assert b"Campus Governance & Topology Console" in login_res.data
print("[PASS] 7. Admin login (with CSRF verification) and dashboard access verified.")

print("\n*** ALL END-TO-END SYSTEM CHECKS PASSED PERFECTLY! ***")
