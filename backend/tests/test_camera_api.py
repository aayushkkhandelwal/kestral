import uuid
import pytest


def test_camera_crud_flow(client, admin_headers):
    # 1. Create Camera
    payload = {
        "camera_name": "ATM Lobby Camera 01",
        "atm_id": "ATM-NYC-101",
        "location": "New York Main Branch",
        "ip_address": "192.168.1.101",
        "status": "online"
    }
    resp = client.post("/api/v1/camera", headers=admin_headers, json=payload)
    assert resp.status_code == 201
    cam = resp.json()
    cam_id = cam["camera_id"]
    assert cam["camera_name"] == payload["camera_name"]
    assert cam["atm_id"] == payload["atm_id"]

    # 2. Get Camera by ID
    resp_get = client.get(f"/api/v1/camera/{cam_id}", headers=admin_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["camera_id"] == cam_id

    # 3. List Cameras with filtering
    resp_list = client.get("/api/v1/camera?atm_id=ATM-NYC-101", headers=admin_headers)
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert list_data["total"] >= 1
    assert any(c["camera_id"] == cam_id for c in list_data["items"])

    # 4. Update Camera
    resp_update = client.put(f"/api/v1/camera/{cam_id}", headers=admin_headers, json={
        "status": "maintenance",
        "location": "New York Main Branch - Vault Entrance"
    })
    assert resp_update.status_code == 200
    assert resp_update.json()["status"] == "maintenance"
    assert resp_update.json()["location"] == "New York Main Branch - Vault Entrance"

    # 5. Delete Camera
    resp_del = client.delete(f"/api/v1/camera/{cam_id}", headers=admin_headers)
    assert resp_del.status_code == 200

    # 6. Verify Deletion
    resp_verify = client.get(f"/api/v1/camera/{cam_id}", headers=admin_headers)
    assert resp_verify.status_code == 404
