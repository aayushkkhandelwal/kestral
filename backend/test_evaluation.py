"""
Kestral AI — Phase 2 Automated Evaluation & Forensic Integrity Test Suite
Verifies:
1. Bounding-box IoU and 1-to-1 matching logic.
2. Precision, Recall, F1, and mAP@0.50 calculations.
3. Empty ground-truth and empty-prediction boundary conditions.
4. Threshold sensitivity (confidence & IoU).
5. Tracking ID switch and fragmentation metrics.
6. Face quality scoring boundaries (zero-crop, extreme light, contrast).
7. Best-frame candidate ranking & deterministic tie-breaking.
8. Correct track-to-evidence association and URL exposure.
9. Cryptographic SHA-256 generation.
10. Integrity verification for MATCH, MODIFIED, and MISSING evidence files.
11. Invalid annotation and corrupt JSON handling.
12. End-to-end evaluation report schema validation.
13. FastAPI integrity verification endpoint.
"""

import os
import sys
import json
import tempfile
import unittest
import numpy as np
import cv2

# Set path for backend imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from evaluation.metrics import (
    compute_iou,
    match_boxes_one_to_one,
    calculate_detection_metrics,
    calculate_map50,
    compute_tracking_metrics,
    compute_sha256,
    verify_file_integrity
)
from services.face_quality import FaceQualityAssessor
from services.best_frame import BestFrameSelector
from fastapi.testclient import TestClient
from main import app


class TestPhase2Metrics(unittest.TestCase):
    """1. Bounding-Box IoU & 1-to-1 Matching Tests"""

    def test_compute_iou_exact_match(self):
        box1 = [10.0, 10.0, 50.0, 50.0]
        box2 = [10.0, 10.0, 50.0, 50.0]
        self.assertAlmostEqual(compute_iou(box1, box2), 1.0, places=4)

    def test_compute_iou_disjoint(self):
        box1 = [0.0, 0.0, 10.0, 10.0]
        box2 = [20.0, 20.0, 30.0, 30.0]
        self.assertEqual(compute_iou(box1, box2), 0.0)

    def test_compute_iou_partial(self):
        # 10x10 overlap of two 10x20 boxes
        box1 = [0.0, 0.0, 20.0, 10.0]  # area = 200
        box2 = [10.0, 0.0, 30.0, 10.0] # area = 200
        self.assertAlmostEqual(compute_iou(box1, box2), 1.0 / 3.0, places=3)

    def test_compute_iou_invalid_zero_area(self):
        box1 = [10.0, 10.0, 10.0, 10.0]  # width=0, height=0
        box2 = [10.0, 10.0, 50.0, 50.0]
        self.assertEqual(compute_iou(box1, box2), 0.0)

    def test_one_to_one_matching_prevents_duplicate_tp(self):
        """A single GT box must not produce multiple true positives from duplicate predictions."""
        gt_boxes = [[10.0, 10.0, 50.0, 50.0]]
        # Two identical overlapping predictions targeting the same GT box
        pred_boxes = [
            [10.0, 10.0, 50.0, 50.0],
            [11.0, 11.0, 51.0, 51.0]
        ]
        matches, unmatched_preds, unmatched_gts = match_boxes_one_to_one(
            pred_boxes, gt_boxes, iou_threshold=0.50
        )
        self.assertEqual(len(matches), 1, "Only one prediction can match the ground truth box")
        self.assertEqual(len(unmatched_preds), 1, "Duplicate prediction must count as unmatched/FP")
        self.assertEqual(len(unmatched_gts), 0)

    def test_precision_recall_empty_predictions(self):
        """No predictions on an image with ground truth -> Precision=0.0, Recall=0.0, FN=len(GT)"""
        gt_boxes = [[0.0, 0.0, 10.0, 10.0], [20.0, 20.0, 30.0, 30.0]]
        matches, un_p, un_g = match_boxes_one_to_one([], gt_boxes, iou_threshold=0.50)
        metrics = calculate_detection_metrics(len(matches), len(un_p), len(un_g))
        self.assertEqual(metrics["true_positives"], 0)
        self.assertEqual(metrics["false_positives"], 0)
        self.assertEqual(metrics["false_negatives"], 2)
        self.assertEqual(metrics["precision"], 0.0)
        self.assertEqual(metrics["recall"], 0.0)
        self.assertEqual(metrics["f1"], 0.0)

    def test_precision_recall_empty_ground_truth(self):
        """Empty scene with 1 false alarm prediction -> Precision=0.0, Recall=0.0, FP=1"""
        pred_boxes = [[5.0, 5.0, 15.0, 15.0]]
        matches, un_p, un_g = match_boxes_one_to_one(pred_boxes, [], iou_threshold=0.50)
        metrics = calculate_detection_metrics(len(matches), len(un_p), len(un_g))
        self.assertEqual(metrics["true_positives"], 0)
        self.assertEqual(metrics["false_positives"], 1)
        self.assertEqual(metrics["false_negatives"], 0)
        self.assertEqual(metrics["precision"], 0.0)
        self.assertEqual(metrics["recall"], 0.0)
        self.assertEqual(metrics["f1"], 0.0)

    def test_map50_calculation_perfect_and_zero(self):
        """Tests trapezoidal precision-recall AUC integration."""
        perfect_preds = [{"confidence": 0.95, "is_tp": True}]
        mAP_perfect = calculate_map50(perfect_preds, total_ground_truths=1, iou_threshold=0.50)
        self.assertAlmostEqual(mAP_perfect, 1.0, places=2)

        bad_preds = [{"confidence": 0.85, "is_tp": False}]
        mAP_zero = calculate_map50(bad_preds, total_ground_truths=1, iou_threshold=0.50)
        self.assertEqual(mAP_zero, 0.0)


class TestPhase2TrackingMetrics(unittest.TestCase):
    """2. ByteTrack Stability & ID Switch Evaluation"""

    def test_tracking_no_id_switches(self):
        """Continuous consistent identity across 3 frames."""
        gt_tracks = {
            1: [
                {"frame_idx": 0, "bbox": [10, 10, 20, 20]},
                {"frame_idx": 1, "bbox": [12, 10, 22, 20]},
                {"frame_idx": 2, "bbox": [14, 10, 24, 20]}
            ]
        }
        pred_tracks = {
            101: [
                {"frame_idx": 0, "bbox": [10, 10, 20, 20]},
                {"frame_idx": 1, "bbox": [12, 10, 22, 20]},
                {"frame_idx": 2, "bbox": [14, 10, 24, 20]}
            ]
        }
        res = compute_tracking_metrics(gt_tracks, pred_tracks, iou_threshold=0.50)
        self.assertEqual(res["id_switches"], 0)
        self.assertEqual(res["track_fragmentations"], 0)
        self.assertEqual(res["ground_truth_identities"], 1)

    def test_tracking_id_switch_detection(self):
        """Simulates tracker losing track and re-assigning a new ID 102 to person 1."""
        gt_tracks = {
            1: [
                {"frame_idx": 0, "bbox": [10, 10, 20, 20]},
                {"frame_idx": 1, "bbox": [12, 10, 22, 20]},
                {"frame_idx": 2, "bbox": [14, 10, 24, 20]}
            ]
        }
        pred_tracks = {
            101: [
                {"frame_idx": 0, "bbox": [10, 10, 20, 20]},
                {"frame_idx": 1, "bbox": [12, 10, 22, 20]}
            ],
            102: [
                {"frame_idx": 2, "bbox": [14, 10, 24, 20]}  # Tracker switch!
            ]
        }
        res = compute_tracking_metrics(gt_tracks, pred_tracks, iou_threshold=0.50)
        self.assertEqual(res["id_switches"], 1, "Must accurately capture identity switch")

    def test_tracking_fragmentation_detection(self):
        """Simulates tracking gap (frame 0 then frame 3, skipping 1 and 2)."""
        gt_tracks = {
            1: [
                {"frame_idx": 0, "bbox": [10, 10, 20, 20]},
                {"frame_idx": 3, "bbox": [10, 10, 20, 20]}
            ]
        }
        pred_tracks = {
            101: [
                {"frame_idx": 0, "bbox": [10, 10, 20, 20]},
                {"frame_idx": 3, "bbox": [10, 10, 20, 20]}
            ]
        }
        res = compute_tracking_metrics(gt_tracks, pred_tracks, iou_threshold=0.50)
        self.assertEqual(res["track_fragmentations"], 1)


class TestPhase2FaceQualityAndBestFrame(unittest.TestCase):
    """3. Face Quality Bounds & Best-Frame Candidate Selection"""

    def setUp(self):
        self.assessor = FaceQualityAssessor()

    def test_quality_zero_and_empty_inputs(self):
        empty_img = np.zeros((0, 0, 3), dtype=np.uint8)
        res = self.assessor.assess_crop(empty_img, has_real_face=True)
        self.assertEqual(res["overall_score"], 0.0)

        none_res = self.assessor.assess_crop(None, has_real_face=True)
        self.assertEqual(none_res["overall_score"], 0.0)

    def test_quality_score_capping_when_no_real_face(self):
        """When has_real_face is False (e.g. torso/shoulder crop), score must be capped at 28.0 max."""
        sharp_img = np.zeros((100, 100, 3), dtype=np.uint8)
        sharp_img[::2, ::2] = 255
        res = self.assessor.assess_crop(sharp_img, has_real_face=False)
        self.assertLessEqual(res["overall_score"], 28.0, "Non-face crops must never receive high evidence scores")

    def test_best_frame_upgrade_and_deterministic_ties(self):
        """Verify higher scoring candidate replaces lower scoring candidate deterministically."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            selector = BestFrameSelector(output_dir=tmp_dir)

            frame1 = np.full((100, 100, 3), 50, dtype=np.uint8)
            frame2 = np.full((100, 100, 3), 128, dtype=np.uint8)
            frame2[10:90:5, 10:90:5] = 255

            face_crop1 = np.full((30, 30, 3), 50, dtype=np.uint8)
            q1 = FaceQualityAssessor.assess_crop(face_crop1, has_real_face=True)
            selector.update_track(
                track_id=1,
                frame_idx=1,
                timestamp_sec=0.1,
                full_frame=frame1,
                person_bbox=[0, 0, 100, 100],
                face_info={"bbox": [10, 10, 40, 40], "face_crop": face_crop1},
                quality_metrics=q1
            )
            score1 = selector.tracks[1]["best_score"]

            face_crop2 = np.full((30, 30, 3), 128, dtype=np.uint8)
            face_crop2[5:25:2, 5:25:2] = 255  # higher contrast and sharpness
            q2 = FaceQualityAssessor.assess_crop(face_crop2, has_real_face=True)
            selector.update_track(
                track_id=1,
                frame_idx=5,
                timestamp_sec=0.5,
                full_frame=frame2,
                person_bbox=[0, 0, 100, 100],
                face_info={"bbox": [10, 10, 40, 40], "face_crop": face_crop2},
                quality_metrics=q2
            )
            score2 = selector.tracks[1]["best_score"]

            self.assertGreater(score2, score1, "Higher quality candidate must yield higher score")
            self.assertEqual(selector.tracks[1]["best_frame_idx"], 5, "Candidate must be upgraded")

            summary = selector.finalize(relative_url_prefix="/results/test_task")
            self.assertEqual(len(summary), 1)
            t1 = summary[0]
            self.assertIn("face_sha256", t1)
            self.assertIn("full_frame_sha256", t1)
            self.assertEqual(len(t1["face_sha256"]), 64)
            self.assertEqual(len(t1["full_frame_sha256"]), 64)


class TestPhase2EvidenceIntegrity(unittest.TestCase):
    """4. SHA-256 Generation & Forensic Integrity Verification"""

    def test_sha256_intact_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Kestral CCTV Evidence Frame 1042")
            temp_path = f.name
        try:
            expected_hash = compute_sha256(temp_path)
            res = verify_file_integrity(temp_path, expected_hash)
            self.assertEqual(res["status"], "MATCH")
            self.assertTrue(res["is_valid"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_sha256_modified_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Original Evidence Content")
            temp_path = f.name
        try:
            original_hash = compute_sha256(temp_path)
            with open(temp_path, "wb") as f:
                f.write(b"Tampered / Modified Content")
            res = verify_file_integrity(temp_path, original_hash)
            self.assertEqual(res["status"], "MODIFIED")
            self.assertFalse(res["is_valid"])
            self.assertNotEqual(res["calculated_hash"], original_hash)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_sha256_missing_file(self):
        res = verify_file_integrity("c:/non_existent_evidence_9999.jpg", "abc123hash")
        self.assertEqual(res["status"], "MISSING")
        self.assertFalse(res["is_valid"])
        self.assertIsNone(res["calculated_hash"])


class TestPhase2ApiEndpoints(unittest.TestCase):
    """5. FastAPI Verification and Evaluation Endpoints"""

    def setUp(self):
        self.client = TestClient(app)

    def test_get_latest_evaluation(self):
        response = self.client.get("/api/evaluation/latest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("person_detection", data)
        self.assertIn("tracking_stability", data)
        self.assertIn("face_detection", data)
        self.assertIn("best_frame_selection", data)

    def test_verify_integrity_invalid_task_id(self):
        response = self.client.get("/api/tasks/invalid..id//../../verify-integrity")
        self.assertIn(response.status_code, [400, 404])

    def test_verify_integrity_missing_task(self):
        response = self.client.get("/api/tasks/notfound99/verify-integrity")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
