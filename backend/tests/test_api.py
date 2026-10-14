"""
Full FastAPI Integration Smoke Tests
Verifies all contract endpoints, database operations, health telemetry, and routers.
"""
import sys
import os
import io
import cv2
import numpy as np
from fastapi.testclient import TestClient

# Ensure backend root on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_health_telemetry():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "cuda_available" in data
    assert data["person_model"] == "yolov8n.pt"
    assert data["face_model_loaded"] is True
    assert data["face_recognizer_loaded"] is True
    print("\n[PASS] /api/health telemetry verified:", data)

def test_stats_no_fake_numbers():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    # With no historical videos, average fidelity must be null/None, never 78.4
    if data["total_videos_analyzed"] == 0:
        assert data["system_average_fidelity"] is None or data["system_average_fidelity"] == 0
    assert "YOLOv8-Tracking" in data["active_models"][0]
    print("[PASS] /api/stats no-fake-numbers verified:", data)

def test_rois_crud():
    polygon = [[100, 100], [400, 100], [400, 500], [100, 500]]
    put_res = client.put("/api/rois/TEST_ATM_1", json={
        "polygon": polygon,
        "frame_width": 1280,
        "frame_height": 720
    })
    assert put_res.status_code == 200
    assert put_res.json()["atm_id"] == "TEST_ATM_1"

    get_res = client.get("/api/rois/TEST_ATM_1")
    assert get_res.status_code == 200
    assert get_res.json()["polygon"] == polygon
    print("[PASS] /api/rois CRUD verified")

def test_transactions_and_audit():
    txn_res = client.post("/api/transactions", json={
        "txn_id": "TXN-TEST-99",
        "atm_id": "TEST_ATM_1",
        "task_id": "non_existent_mock_task",
        "start_s": 5.0,
        "end_s": 15.0
    })
    assert txn_res.status_code == 200
    txn_data = txn_res.json()
    assert txn_data["txn_id"] == "TXN-TEST-99"

    list_res = client.get("/api/transactions?atm_id=TEST_ATM_1")
    assert list_res.status_code == 200
    assert any(t["txn_id"] == "TXN-TEST-99" for t in list_res.json())

    # Verify audit logs
    audit_res = client.get("/api/audit")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0
    print(f"[PASS] /api/transactions & /api/audit verified ({len(logs)} audit entries recorded)")

def test_face_search_endpoint():
    # Create synthetic test image probe
    probe_img = np.full((120, 120, 3), 120, dtype=np.uint8)
    cv2.circle(probe_img, (40, 50), 10, (20, 20, 20), -1)
    cv2.circle(probe_img, (80, 50), 10, (20, 20, 20), -1)
    _, encoded = cv2.imencode(".jpg", probe_img)

    res = client.post(
        "/api/search/face?top_k=3",
        files={"file": ("probe.jpg", io.BytesIO(encoded.tobytes()), "image/jpeg")}
    )
    assert res.status_code == 200
    matches = res.json()
    assert isinstance(matches, list)
    if len(matches) > 0:
        assert "similarity only; needs human review" in matches[0]["note"]
    print(f"[PASS] /api/search/face verified (returned {len(matches)} matches)")

if __name__ == "__main__":
    test_health_telemetry()
    test_stats_no_fake_numbers()
    test_rois_crud()
    test_transactions_and_audit()
    test_face_search_endpoint()
    print("\n[ALL PASS] All FastAPI integration tests succeeded!")
