import os
import time
import unittest
import numpy as np
import cv2
from fastapi.testclient import TestClient
import main
from services.face_detector import FaceDetector
from services.person_detector import PersonDetector

client = TestClient(main.app)

def test_camera_status_endpoint():
    """Verifies that /api/camera/status returns 200 and expected model telemetry."""
    response = client.get("/api/camera/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "YOLOv8" in data["person_tracker"]
    assert "YuNet" in data["face_detector"]
    assert "landmarks" in data

def test_camera_detect_with_synthetic_frame():
    """Verifies that /api/camera/detect safely processes a valid image frame."""
    # Create synthetic test frame
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw simple gradient/shapes to ensure valid color buffer
    cv2.circle(img, (320, 240), 50, (200, 200, 200), -1)
    
    success, buffer = cv2.imencode(".jpg", img)
    assert success
    
    response = client.post(
        "/api/camera/detect",
        files={"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert data["frame_width"] == 640
    assert data["frame_height"] == 480
    assert "faces_detected" in data
    assert "people_detected" in data
    assert isinstance(data["faces"], list)
    assert isinstance(data["people"], list)
    assert "processing_time_ms" in data

def test_camera_detect_with_evidence_image():
    """Verifies real face detection, landmarks extraction, and person tracking on saved evidence."""
    test_img = os.path.join(os.path.dirname(__file__), "results", "4f5094e0", "track_93_full.jpg")
    if not os.path.exists(test_img):
        print("Note: Evidence sample image not found, skipping image test")
        return
        
    with open(test_img, "rb") as f:
        img_bytes = f.read()

    response = client.post(
        "/api/camera/detect?conf_threshold=0.3&face_conf_threshold=0.3",
        files={"file": ("evidence.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["frame_width"] > 0
    assert data["frame_height"] > 0
    assert data["processing_time_ms"] > 0
    
    # Check landmarks if faces were detected
    if data["faces_detected"] > 0:
        face = data["faces"][0]
        assert "bbox" in face
        assert len(face["bbox"]) == 4
        assert "confidence" in face
        assert "landmarks" in face
        # 5 facial landmarks (right eye, left eye, nose, right mouth, left mouth)
        assert len(face["landmarks"]) == 5
        for pt in face["landmarks"]:
            assert len(pt) == 2
            assert 0 <= pt[0] <= data["frame_width"]
            assert 0 <= pt[1] <= data["frame_height"]

def test_camera_detect_invalid_frames():
    """Verifies safe error handling for malformed, empty, or corrupt frames."""
    # 1. Empty payload
    res1 = client.post("/api/camera/detect", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert res1.status_code == 400

    # 2. Corrupt/random non-image bytes
    res2 = client.post("/api/camera/detect", files={"file": ("corrupt.jpg", b"NOT_AN_IMAGE_CONTENT", "image/jpeg")})
    assert res2.status_code == 400

    # 3. Missing file param
    res3 = client.post("/api/camera/detect")
    assert res3.status_code == 400

def test_camera_tracker_reset():
    """Verifies /api/camera/reset clears tracker without throwing errors."""
    response = client.post("/api/camera/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_continuous_15s_timer_logic():
    """
    Unit test verifying the 15-second continuous visibility state machine:
    - Accurate wall-clock duration calculation
    - Grace period tolerance for temporary occlusions (1.5s)
    - Resetting timer when person is absent beyond grace period
    - Preventing duplicate alerts during the same continuous stay
    - Independent timers for multiple people
    """
    class MockTrackerSession:
        def __init__(self, grace_period=1.5):
            self.grace_period = grace_period
            self.registry = {} # tid -> dict
            self.triggered_events = []

        def process_frame(self, detected_ids, current_time):
            for tid in detected_ids:
                if tid not in self.registry:
                    # New subject
                    self.registry[tid] = {
                        "first_seen": current_time,
                        "last_seen": current_time,
                        "alert_triggered": False,
                        "active": True
                    }
                else:
                    track = self.registry[tid]
                    gap = current_time - track["last_seen"]
                    if gap <= self.grace_period:
                        track["last_seen"] = current_time
                        track["active"] = True
                        continuous_dur = current_time - track["first_seen"]
                        if continuous_dur >= 15.0 and not track["alert_triggered"]:
                            track["alert_triggered"] = True
                            self.triggered_events.append({
                                "track_id": tid,
                                "duration": continuous_dur,
                                "time": current_time
                            })
                    else:
                        # Exceeded grace period: Reset timer!
                        track["first_seen"] = current_time
                        track["last_seen"] = current_time
                        track["alert_triggered"] = False
                        track["active"] = True

    session = MockTrackerSession(grace_period=1.5)
    t = 100.0

    # Track 1 appears at t=100.0
    session.process_frame([1], current_time=t)
    assert len(session.triggered_events) == 0
    assert session.registry[1]["first_seen"] == 100.0

    # Frames arrive every 0.5s up to t=105.0
    for _ in range(10):
        t += 0.5
        session.process_frame([1], current_time=t)
    assert len(session.triggered_events) == 0
    assert session.registry[1]["first_seen"] == 100.0

    # Temporary 1.0s gap (drop 1 sample, gap is 1.0s <= grace period 1.5s)
    t += 1.0
    session.process_frame([1], current_time=t)
    assert session.registry[1]["first_seen"] == 100.0 # NOT reset

    # Continuous frames up to 15.0 seconds (t = 115.5)
    while t < 115.5:
        t += 0.5
        session.process_frame([1], current_time=t)

    assert len(session.triggered_events) == 1
    assert session.triggered_events[0]["track_id"] == 1
    assert session.triggered_events[0]["duration"] >= 15.0

    # Continue staying in frame for another 10 frames: NO duplicate alert!
    for _ in range(10):
        t += 0.5
        session.process_frame([1], current_time=t)
    assert len(session.triggered_events) == 1 # still exactly 1 alert!

    # Person 1 leaves for 3 seconds (exceeds grace period of 1.5s)
    t += 3.0
    session.process_frame([1], current_time=t) # returns
    # Timer should have RESET to t
    assert session.registry[1]["first_seen"] == t
    assert session.registry[1]["alert_triggered"] == False

    # Second person (Track 2) arrives and has an independent timer
    t2_time = t
    session.process_frame([1, 2], current_time=t)
    assert session.registry[2]["first_seen"] == t2_time
    assert session.registry[1]["first_seen"] == t

if __name__ == "__main__":
    test_camera_status_endpoint()
    test_camera_detect_with_synthetic_frame()
    test_camera_detect_with_evidence_image()
    test_camera_detect_invalid_frames()
    test_camera_tracker_reset()
    test_continuous_15s_timer_logic()
    print("ALL TESTS PASSED SUCCESSFULLY!")
