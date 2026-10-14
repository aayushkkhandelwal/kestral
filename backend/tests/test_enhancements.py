"""
Unit Tests for Mentoring Feedback Enhancements
Covers:
1. Deblurring & sharpening restoration
2. Multi-angle composite generation
3. Database evidence_faces persistence and query
4. Targeted window frame math
"""
import sys
import os
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
import config
from services.face_quality import FaceQualityAssessor
from services.best_frame import BestFrameSelector

def test_deblur_and_sharpen_image():
    assessor = FaceQualityAssessor()
    
    # Create synthetic face
    base = np.full((120, 120, 3), 128, dtype=np.uint8)
    cv2.circle(base, (40, 50), 10, (20, 20, 20), -1)
    cv2.circle(base, (80, 50), 10, (20, 20, 20), -1)
    cv2.line(base, (60, 60), (60, 80), (30, 30, 30), 3)

    # Blur it heavily
    blurred = cv2.GaussianBlur(base, (11, 11), 3.5)
    raw_laplacian = cv2.Laplacian(cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()

    # Apply deblurring
    deblurred = assessor.deblur_and_sharpen_image(blurred)
    deblurred_laplacian = cv2.Laplacian(cv2.cvtColor(deblurred, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()

    assert deblurred is not None
    assert deblurred.shape == blurred.shape
    # Deblurred image should restore high-frequency contrast (higher Laplacian variance)
    assert deblurred_laplacian > raw_laplacian, f"Deblurred ({deblurred_laplacian}) should exceed raw blurry ({raw_laplacian})"

def test_multi_angle_composite_generation():
    selector = BestFrameSelector(output_dir="/tmp")

    # Create dummy candidate crops with different poses
    crop1 = np.full((100, 100, 3), 120, dtype=np.uint8)
    crop2 = np.full((100, 100, 3), 140, dtype=np.uint8)
    crop3 = np.full((100, 100, 3), 160, dtype=np.uint8)

    runner_ups = [
        {"face_crop": crop1, "score": 75.0, "quality": {"yaw_proxy": -0.25}},
        {"face_crop": crop3, "score": 70.0, "quality": {"yaw_proxy": 0.30}},
    ]

    comp_filename = selector._generate_multi_angle_composite(best_crop=crop2, runner_ups=runner_ups, track_id=99)
    assert comp_filename is not None
    assert comp_filename == "track_99_composite.jpg"
    comp_path = os.path.join("/tmp", comp_filename)
    assert os.path.exists(comp_path)
    composite = cv2.imread(comp_path)
    assert composite is not None
    h, w, c = composite.shape
    assert c == 3
    assert w >= 300, f"Composite width ({w}) should accommodate multiple angles"
    assert h >= 100
    if os.path.exists(comp_path):
        os.remove(comp_path)

def test_evidence_faces_db_crud():
    # Test saving and reading back from SQLite
    test_task_id = "test_task_99"
    test_track_id = 99
    atm_id = "ATM_TEST_01"
    location = "Test Branch ATM"
    timestamp_s = 42.5
    wall_clock = "2026-10-14 12:00:00 UTC"
    face_url = "/results/test/track_99_face.jpg"
    full_url = "/results/test/frame_0042.jpg"
    quality_score = 91.5
    embedding = [0.1] * 128

    save_res = db.save_evidence_face(
        task_id=test_task_id,
        track_id=test_track_id,
        atm_id=atm_id,
        location_name=location,
        timestamp_s=timestamp_s,
        wall_clock_time=wall_clock,
        face_image_url=face_url,
        full_frame_url=full_url,
        quality_score=quality_score,
        has_real_face=True,
        embedding=embedding,
        enhanced_image_url="/results/test/track_99_enhanced.jpg",
        composite_image_url="/results/test/track_99_composite.jpg"
    )
    assert save_res["status"] == "saved"

    # Query back
    faces = db.get_all_evidence_faces(atm_id=atm_id)
    matched = [f for f in faces if f["face_id"] == f"{test_task_id}_{test_track_id}"]
    assert len(matched) == 1
    m = matched[0]
    assert m["atm_id"] == atm_id
    assert m["location_name"] == location
    assert m["quality_score"] == quality_score
    assert len(m["embedding"]) == 128
    assert m["enhanced_image_url"] == "/results/test/track_99_enhanced.jpg"
    assert m["composite_image_url"] == "/results/test/track_99_composite.jpg"

def test_targeted_window_bounds():
    fps = 30.0
    total_frames = 18000 # 10 minute video
    target_time_s = 300.0 # 5 minutes in
    window_margin_s = 60.0 # +/- 1 min

    window_start_s = max(0.0, target_time_s - window_margin_s)
    window_end_s = target_time_s + window_margin_s
    start_frame = int(window_start_s * fps)
    end_frame = min(total_frames, int(window_end_s * fps))

    assert window_start_s == 240.0 # 4m
    assert window_end_s == 360.0   # 6m
    assert start_frame == 7200
    assert end_frame == 10800
    frames_to_process = end_frame - start_frame
    assert frames_to_process == 3600 # 2 mins instead of 18,000 frames (80% compute saved!)
