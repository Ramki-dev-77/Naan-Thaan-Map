"""
Campus Navigation System — Admin & Security Test Suite
Tests authentication, authorization, CRUD operations, and immutable audit logs.
"""
import json
from app.models.audit import AuditLog
from app.models.building import Building


def test_admin_unauthorized_access(client):
    """Access to admin API without login must return 401."""
    res = client.post("/api/v1/admin/buildings", data=json.dumps({}), content_type="application/json")
    assert res.status_code == 401
    data = res.get_json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_admin_login_success(client):
    """Valid credentials allow login and session establishment."""
    payload = {
        "username": "admin",
        "password": "CampusAdmin2026!"
    }
    res = client.post("/api/v1/admin/login", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["user"]["username"] == "admin"


def test_admin_building_crud_and_audit(client):
    """Admin can create building and it generates an immutable AuditLog entry."""
    # 1. Login
    client.post("/api/v1/admin/login", data=json.dumps({
        "username": "admin",
        "password": "CampusAdmin2026!"
    }), content_type="application/json")

    # 2. Create Building
    payload = {
        "campus_id": 1,
        "name": "Biotechnology Research Pavilion",
        "code": "BTR",
        "description": "Genomics and Bio-engineering research facilities.",
        "latitude": 12.9725,
        "longitude": 77.5930,
        "floors": 3,
        "accessible": True
    }
    res = client.post("/api/v1/admin/buildings", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 201
    b_data = res.get_json()["data"]
    assert b_data["code"] == "BTR"

    # 3. Check AuditLog entry
    audit_res = client.get("/api/v1/admin/audit-logs")
    assert audit_res.status_code == 200
    logs = audit_res.get_json()["data"]
    assert len(logs) > 0
    actions = [l["action"] for l in logs]
    assert "CREATE_BUILDING" in actions
