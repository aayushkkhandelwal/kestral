import pytest
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository


def test_alerts_and_acknowledgement(client, officer_headers, test_officer_user):
    # 1. Trigger Alert
    alert_payload = {
        "alert_type": "LOITERING_DETECTED",
        "severity": "high",
        "message": "Subject loitering near ATM vestibule for over 8 minutes."
    }
    resp = client.post("/api/v1/alerts", headers=officer_headers, json=alert_payload)
    assert resp.status_code == 201
    alert_data = resp.json()
    alert_id = alert_data["alert_id"]
    assert alert_data["alert_type"] == "LOITERING_DETECTED"
    assert alert_data["severity"] == "high"

    # 2. List Alerts
    list_resp = client.get("/api/v1/alerts?severity=high", headers=officer_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 3. Acknowledge Alert
    ack_resp = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers=officer_headers, json={
        "note": "Dispatched security patrol unit to verify area."
    })
    assert ack_resp.status_code == 200
    ack_data = ack_resp.json()
    assert ack_data["is_acknowledged"] is True
    assert ack_data["acknowledged_by"] == str(test_officer_user.id)


def test_audit_logs_recording(db, test_admin_user):
    repo = AuditRepository(db)
    repo.record_action(
        action="user.login",
        resource="auth",
        user_id=test_admin_user.id,
        request_id="req-999",
        details={"ip": "127.0.0.1"}
    )
    db.commit()

    logs, total = repo.list_logs(user_id=test_admin_user.id)
    assert total >= 1
    assert any(l.action == "user.login" for l in logs)
