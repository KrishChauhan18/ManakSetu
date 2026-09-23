import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

# Helper token generators
def get_auth_headers(role: str, user_id: int):
    token = create_access_token(subject=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_list_rules():
    response = client.get("/rules/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_dashboard_stats():
    response = client.get("/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_scans" in data
    assert "overall_compliance_pct" in data

def test_api_scan_endpoint():
    import cv2
    import numpy as np
    
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Net Qty: 500g MRP Rs 100", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    _, encoded = cv2.imencode(".jpg", img)
    img_bytes = encoded.tobytes()

    response = client.post(
        "/api/scan",
        files={"file": ("test_label.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert "scan_id" in res_data
    assert "compliance" in res_data

# RBAC 403 Permission Denied Tests
def test_inspector_cannot_create_rule():
    headers = get_auth_headers(role="inspector", user_id=3)
    rule_payload = {
        "rule_id_str": "TEST-INSPECTOR-RULE",
        "field": "test",
        "check_type": "presence",
        "severity": "high",
        "category": ["all"],
        "version": "2011"
    }
    res = client.post("/rules/", json=rule_payload, headers=headers)
    assert res.status_code == 403

def test_inspector_cannot_access_audit_logs():
    headers = get_auth_headers(role="inspector", user_id=3)
    res = client.get("/audit/", headers=headers)
    assert res.status_code == 403

def test_inspector_cannot_list_users():
    headers = get_auth_headers(role="inspector", user_id=3)
    res = client.get("/users/", headers=headers)
    assert res.status_code == 403

def test_supervisor_cannot_delete_scan():
    headers = get_auth_headers(role="supervisor", user_id=2)
    res = client.delete("/scan/99999", headers=headers)
    assert res.status_code == 403

def test_supervisor_cannot_create_user():
    headers = get_auth_headers(role="supervisor", user_id=2)
    user_payload = {
        "email": "unauthorized_user@complyerg.gov.in",
        "password": "Password@123",
        "role": "inspector"
    }
    res = client.post("/users/", json=user_payload, headers=headers)
    assert res.status_code == 403

# Admin Allowed Tests
def test_admin_can_access_audit_logs():
    headers = get_auth_headers(role="admin", user_id=1)
    res = client.get("/audit/", headers=headers)
    assert res.status_code == 200

def test_admin_can_list_users():
    headers = get_auth_headers(role="admin", user_id=1)
    res = client.get("/users/", headers=headers)
    assert res.status_code == 200
