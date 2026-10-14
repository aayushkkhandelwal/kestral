import pytest


def test_legacy_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["online", "healthy"]


def test_legacy_stats_endpoint(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_videos_analyzed" in data
    assert "total_persons_tracked" in data
    assert "high_quality_evidence_captured" in data
    assert "active_models" in data


def test_legacy_history_endpoint(client):
    resp = client.get("/api/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_legacy_camera_status_and_reset(client):
    status_resp = client.get("/api/camera/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "online"

    reset_resp = client.post("/api/camera/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "ok"
