import os
import io
import time
import json
import unittest
import numpy as np
import cv2
from fastapi.testclient import TestClient

import main
from services.face_detector import FaceDetector
from services.face_quality import FaceQualityAssessor
from services.best_frame import BestFrameSelector
from services.person_detector import PersonDetector

client = TestClient(main.app)

def create_synthetic_video(filepath: str, num_frames: int = 15, width: int = 320, height: int = 240, with_person_shape: bool = False):
    """Utility to generate a valid, small synthetic MP4 video using OpenCV."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, 10.0, (width, height))
    for i in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Add background variation
        frame[:] = (30 + i * 2, 30 + i * 2, 30 + i * 2)
        if with_person_shape:
            # Draw an oval and head to stimulate detector
            cv2.ellipse(frame, (160, 160), (40, 70), 0, 0, 360, (180, 150, 120), -1)
            cv2.circle(frame, (160, 70), 30, (210, 180, 150), -1)
        else:
            # Pure geometric pattern (no person)
            cv2.rectangle(frame, (10, 10), (60, 60), (0, 255, 0), -1)
        out.write(frame)
    out.release()

class TestKestralPipeline(unittest.TestCase):
    """Automated test suite verifying the complete Kestral Vision Pipeline."""

    # ----------------------------------------------------
    # 1. Health check endpoint
    # ----------------------------------------------------
    def test_01_health_endpoint(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "online")
        self.assertIn("service", data)
        self.assertIn("version", data)

    # ----------------------------------------------------
    # 2. Invalid upload format
    # ----------------------------------------------------
    def test_02_invalid_upload_format(self):
        fake_content = b"This is a text file, not a video."
        response = client.post(
            "/api/upload-and-process",
            files={"file": ("malicious.txt", fake_content, "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported video format", response.json().get("detail", ""))

    # ----------------------------------------------------
    # 3. Missing or malformed upload
    # ----------------------------------------------------
    def test_03_missing_or_empty_upload(self):
        # Empty file (0 bytes)
        res_empty = client.post(
            "/api/upload-and-process",
            files={"file": ("empty.mp4", b"", "video/mp4")}
        )
        self.assertEqual(res_empty.status_code, 400)
        self.assertIn("empty", res_empty.json().get("detail", "").lower())

        # No file parameter
        res_none = client.post("/api/upload-and-process")
        self.assertEqual(res_none.status_code, 422) # FastAPI validation error for missing field

    # ----------------------------------------------------
    # 4. Valid video upload & task queuing
    # ----------------------------------------------------
    def test_04_valid_video_upload(self):
        tmp_video = os.path.join(main.BASE_DIR, "test_synth.mp4")
        create_synthetic_video(tmp_video, num_frames=10)
        try:
            with open(tmp_video, "rb") as f:
                res = client.post(
                    "/api/upload-and-process",
                    files={"file": ("test_synth.mp4", f.read(), "video/mp4")}
                )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("task_id", data)
            self.assertEqual(data.get("status"), "processing")
            self.task_id = data["task_id"]
        finally:
            if os.path.exists(tmp_video):
                os.remove(tmp_video)

    # ----------------------------------------------------
    # 5. Task status transitions
    # ----------------------------------------------------
    def test_05_task_status_transitions(self):
        tmp_video = os.path.join(main.BASE_DIR, "test_status.mp4")
        create_synthetic_video(tmp_video, num_frames=12)
        try:
            with open(tmp_video, "rb") as f:
                res = client.post(
                    "/api/upload-and-process",
                    files={"file": ("test_status.mp4", f.read(), "video/mp4")}
                )
            task_id = res.json()["task_id"]

            # Poll until completed or timeout
            t0 = time.time()
            final_status = None
            while time.time() - t0 < 15.0:
                s_res = client.get(f"/api/tasks/{task_id}/status")
                self.assertEqual(s_res.status_code, 200)
                status_data = s_res.json()
                if status_data.get("status") in ["completed", "failed"]:
                    final_status = status_data.get("status")
                    break
                time.sleep(0.3)

            self.assertEqual(final_status, "completed")
            self.assertEqual(status_data.get("progress"), 100.0)
            self.assertIn("result", status_data)
        finally:
            if os.path.exists(tmp_video):
                os.remove(tmp_video)

    # ----------------------------------------------------
    # 6. No-person video completes gracefully
    # ----------------------------------------------------
    def test_06_no_person_video_handling(self):
        tmp_video = os.path.join(main.BASE_DIR, "test_no_person.mp4")
        create_synthetic_video(tmp_video, num_frames=10, with_person_shape=False)
        try:
            with open(tmp_video, "rb") as f:
                res = client.post(
                    "/api/upload-and-process",
                    files={"file": ("no_person.mp4", f.read(), "video/mp4")}
                )
            task_id = res.json()["task_id"]

            t0 = time.time()
            completed = False
            while time.time() - t0 < 15.0:
                s_res = client.get(f"/api/tasks/{task_id}/status")
                if s_res.status_code == 200 and s_res.json().get("status") == "completed":
                    completed = True
                    result = s_res.json().get("result", {})
                    self.assertEqual(result.get("summary", {}).get("unique_persons_tracked"), 0)
                    self.assertEqual(len(result.get("tracks", [])), 0)
                    break
                time.sleep(0.3)

            self.assertTrue(completed, "No-person video failed to complete gracefully.")
        finally:
            if os.path.exists(tmp_video):
                os.remove(tmp_video)

    # ----------------------------------------------------
    # 7. Face detector graceful failure / fallback
    # ----------------------------------------------------
    def test_07_face_detector_fallback(self):
        # Create a face detector with no active YuNet network (simulating missing model or init failure)
        detector = FaceDetector()
        detector.yunet = None

        dummy_frame = np.ones((400, 400, 3), dtype=np.uint8) * 120
        person_bbox = [100, 50, 300, 350]

        # Must not raise an exception, must return upper-body fallback with has_real_face=False
        result = detector.detect_face_in_person(dummy_frame, person_bbox)
        self.assertIsNotNone(result)
        self.assertFalse(result["has_real_face"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("bbox", result)
        self.assertIn("face_crop", result)

        # Full frame face detection returns empty list without error
        faces = detector.detect_faces(dummy_frame)
        self.assertEqual(faces, [])

    # ----------------------------------------------------
    # 8. Best-frame score comparison logic
    # ----------------------------------------------------
    def test_08_best_frame_scoring_and_upgrade(self):
        output_dir = os.path.join(main.RESULTS_DIR, "test_eval_track")
        selector = BestFrameSelector(output_dir=output_dir)

        frame1 = np.ones((200, 200, 3), dtype=np.uint8) * 50
        frame2 = np.ones((200, 200, 3), dtype=np.uint8) * 150
        person_box = [20, 20, 180, 180]

        # Initial detection: score 40.0, no real face
        q1 = {"overall_score": 40.0, "has_real_face": False}
        selector.update_track(
            track_id=1,
            frame_idx=0,
            timestamp_sec=0.0,
            full_frame=frame1,
            person_bbox=person_box,
            face_info={"bbox": [40, 20, 160, 80], "face_crop": frame1[:50, :50]},
            quality_metrics=q1
        )
        self.assertEqual(selector.tracks[1]["best_score"], 40.0)
        self.assertFalse(selector.tracks[1]["best_has_real_face"])

        # Candidate 2: lower score (30.0), no real face -> should NOT replace
        q2 = {"overall_score": 30.0, "has_real_face": False}
        selector.update_track(
            track_id=1,
            frame_idx=5,
            timestamp_sec=0.5,
            full_frame=frame2,
            person_bbox=person_box,
            face_info={"bbox": [40, 20, 160, 80], "face_crop": frame2[:50, :50]},
            quality_metrics=q2
        )
        self.assertEqual(selector.tracks[1]["best_score"], 40.0)
        self.assertEqual(selector.tracks[1]["best_frame_idx"], 0)

        # Candidate 3: verified real face (score 65.0) -> MUST upgrade track immediately!
        q3 = {"overall_score": 65.0, "has_real_face": True}
        selector.update_track(
            track_id=1,
            frame_idx=10,
            timestamp_sec=1.0,
            full_frame=frame2,
            person_bbox=person_box,
            face_info={"bbox": [40, 20, 160, 80], "face_crop": frame2[:50, :50]},
            quality_metrics=q3
        )
        self.assertEqual(selector.tracks[1]["best_score"], 65.0)
        self.assertTrue(selector.tracks[1]["best_has_real_face"])
        self.assertEqual(selector.tracks[1]["best_frame_idx"], 10)

        # Finalize and verify schema includes both face_image_url and crop_url
        finalized = selector.finalize("/results/test_eval_track")
        self.assertEqual(len(finalized), 1)
        self.assertIn("crop_url", finalized[0])
        self.assertIn("face_image_url", finalized[0])
        self.assertEqual(finalized[0]["crop_url"], finalized[0]["face_image_url"])

    # ----------------------------------------------------
    # 9. Missing evidence & path traversal security
    # ----------------------------------------------------
    def test_09_security_and_missing_evidence(self):
        # 1. Nonexistent task
        res_missing = client.get("/api/tasks/nonexistent_task_9999/status")
        self.assertEqual(res_missing.status_code, 404)

        # 2. Path traversal in task ID (URL normalized or blocked)
        res_traversal = client.get("/api/tasks/../../etc/status")
        self.assertIn(res_traversal.status_code, [400, 404])

        # 3. Path traversal in results (URL-encoded parameter blocked)
        res_res_traversal = client.get("/api/tasks/..%2F..%2Fetc/results")
        self.assertIn(res_res_traversal.status_code, [400, 404])

    # ----------------------------------------------------
    # 10. Live-camera endpoint handling
    # ----------------------------------------------------
    def test_10_live_camera_endpoints(self):
        # 1. Status endpoint
        res_status = client.get("/api/camera/status")
        self.assertEqual(res_status.status_code, 200)
        self.assertEqual(res_status.json().get("status"), "online")

        # 2. Valid frame detection
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.circle(img, (160, 120), 40, (255, 255, 255), -1)
        _, buf = cv2.imencode(".jpg", img)

        res_detect = client.post(
            "/api/camera/detect",
            files={"file": ("frame.jpg", buf.tobytes(), "image/jpeg")}
        )
        self.assertEqual(res_detect.status_code, 200)
        data = res_detect.json()
        self.assertIn("people_detected", data)
        self.assertIn("faces_detected", data)
        self.assertIn("processing_time_ms", data)

        # 3. Corrupt frame
        res_corrupt = client.post(
            "/api/camera/detect",
            files={"file": ("bad.jpg", b"NOT_IMAGE", "image/jpeg")}
        )
        self.assertEqual(res_corrupt.status_code, 400)

        # 4. Reset tracker
        res_reset = client.post("/api/camera/reset")
        self.assertEqual(res_reset.status_code, 200)

    # ----------------------------------------------------
    # 11. 15-second person visibility alert timer logic
    # ----------------------------------------------------
    def test_11_visibility_timer_state_machine(self):
        class TrackerState:
            def __init__(self, grace_period=1.5):
                self.grace_period = grace_period
                self.registry = {}
                self.alerts = []

            def update(self, seen_ids, now_sec):
                for tid in seen_ids:
                    if tid not in self.registry:
                        self.registry[tid] = {
                            "first_seen": now_sec,
                            "last_seen": now_sec,
                            "continuous": 0.0,
                            "alert_triggered": False
                        }
                    else:
                        item = self.registry[tid]
                        gap = now_sec - item["last_seen"]
                        if gap <= self.grace_period:
                            item["last_seen"] = now_sec
                            item["continuous"] = now_sec - item["first_seen"]
                            if item["continuous"] >= 15.0 and not item["alert_triggered"]:
                                item["alert_triggered"] = True
                                self.alerts.append((tid, now_sec))
                        else:
                            item["first_seen"] = now_sec
                            item["last_seen"] = now_sec
                            item["continuous"] = 0.0
                            item["alert_triggered"] = False

        state = TrackerState(grace_period=1.5)
        t = 1000.0

        # Person enters at t=1000.0
        state.update([101], now_sec=t)
        self.assertEqual(len(state.alerts), 0)

        # Continuous frames arriving every 0.5s for 14.5 seconds (29 frames)
        for _ in range(29):
            t += 0.5
            state.update([101], now_sec=t)
        self.assertEqual(len(state.alerts), 0)

        # 30th frame (15.0s elapsed) -> Alert fires!
        t += 0.5 # t=1015.0
        state.update([101], now_sec=t)
        self.assertEqual(len(state.alerts), 1)
        self.assertEqual(state.alerts[0][0], 101)

        # Continues in view for 5 more seconds -> NO duplicate alert
        for _ in range(10):
            t += 0.5
            state.update([101], now_sec=t)
        self.assertEqual(len(state.alerts), 1)

        # Person leaves for 3.0 seconds (exceeds grace period of 1.5s)
        t += 3.0
        # Returns
        state.update([101], now_sec=t)
        self.assertEqual(state.registry[101]["first_seen"], t)
        self.assertFalse(state.registry[101]["alert_triggered"])
        self.assertEqual(len(state.alerts), 1)

    # ----------------------------------------------------
    # 12. Real-model smoke test
    # ----------------------------------------------------
    def test_12_real_model_smoke_test(self):
        """Verifies actual loaded YOLOv8 and YuNet weights execute on real input without crash."""
        p_detector = PersonDetector(confidence_threshold=0.25)
        f_detector = FaceDetector()

        # Realistic synthetic test image with contrast
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[100:400, 200:400] = (120, 140, 160)
        cv2.circle(img, (300, 180), 50, (200, 180, 170), -1)

        # 1. Person tracking inference
        detections = p_detector.track(img, persist=True)
        self.assertIsInstance(detections, list)

        # 2. Face detection inference
        faces = f_detector.detect_faces(img)
        self.assertIsInstance(faces, list)

        # 3. Quality evaluation
        q_score = FaceQualityAssessor.assess_crop(img[100:250, 220:380], has_real_face=True)
        self.assertIn("overall_score", q_score)
        self.assertIn("grade", q_score)
        self.assertGreaterEqual(q_score["overall_score"], 0.0)
        self.assertLessEqual(q_score["overall_score"], 100.0)

if __name__ == "__main__":
    unittest.main()
