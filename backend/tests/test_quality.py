"""
Unit Tests for Quality v2 Biometric Scoring (Task T2.6)
Validates ordering and sub-scores for sharp, blurry, dark, and side-angle face captures.
"""
import sys
import os
import cv2
import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.face_quality import FaceQualityAssessor

def create_synthetic_face(base_val: int = 128) -> np.ndarray:
    """Generates a synthetic 160x160 face-like pattern with sharp edges."""
    img = np.full((160, 160, 3), base_val, dtype=np.uint8)
    # Add high-contrast facial features (eyes, nose, mouth)
    cv2.circle(img, (50, 60), 12, (20, 20, 20), -1)   # Right eye
    cv2.circle(img, (110, 60), 12, (20, 20, 20), -1)  # Left eye
    cv2.line(img, (80, 75), (80, 95), (30, 30, 30), 4)  # Nose
    cv2.rectangle(img, (55, 115), (105, 125), (40, 40, 40), -1) # Mouth
    # Add cheek texture gradients
    cv2.line(img, (30, 40), (130, 40), (220, 220, 220), 2)
    return img

def test_quality_ordering_and_flags():
    assessor = FaceQualityAssessor()

    # 1. Sharp frontal face
    sharp_face = create_synthetic_face(130)
    frontal_landmarks = [[50, 60], [110, 60], [80, 85], [55, 120], [105, 120]]
    res_sharp = assessor.assess_crop(sharp_face, has_real_face=True, landmarks=frontal_landmarks, detector_conf=0.90)

    # 2. Blurry face (severe Gaussian blur)
    blurry_face = cv2.GaussianBlur(sharp_face, (25, 25), 9.0)
    res_blurry = assessor.assess_crop(blurry_face, has_real_face=True, landmarks=frontal_landmarks, detector_conf=0.75)

    # 3. Dark underexposed face
    dark_face = (sharp_face * 0.18).astype(np.uint8)
    res_dark = assessor.assess_crop(dark_face, has_real_face=True, landmarks=frontal_landmarks, detector_conf=0.60)

    # 4. Side-angle face (nose shifted laterally towards edge)
    side_landmarks = [[50, 60], [110, 60], [125, 85], [75, 120], [115, 120]]
    res_side = assessor.assess_crop(sharp_face, has_real_face=True, landmarks=side_landmarks, detector_conf=0.85)

    # 5. Non-face background crop
    non_face = np.full((100, 100, 3), 110, dtype=np.uint8)
    res_non_face = assessor.assess_crop(non_face, has_real_face=False)

    print("\n--- Quality v2 Benchmark Sub-Scores ---")
    print(f"Sharp Frontal:  Score={res_sharp['overall_score']} | Sharpness={res_sharp['sharpness_normalized']} | Pose={res_sharp['pose_score']} | Flags={res_sharp['flags']}")
    print(f"Blurry Frontal: Score={res_blurry['overall_score']} | Sharpness={res_blurry['sharpness_normalized']} | Flags={res_blurry['flags']}")
    print(f"Dark Face:      Score={res_dark['overall_score']} | Brightness={res_dark['brightness']} | Enhanced={res_dark['enhanced']} | Flags={res_dark['flags']}")
    print(f"Side-Angle:     Score={res_side['overall_score']} | YawProxy={res_side['yaw_proxy']} | Pose={res_side['pose_score']} | Flags={res_side['flags']}")
    print(f"No Real Face:   Score={res_non_face['overall_score']} | Flags={res_non_face['flags']}")

    # Verifications
    assert res_sharp["overall_score"] > res_blurry["overall_score"], "Sharp crop must score higher than blurry crop"
    assert res_sharp["overall_score"] > res_side["overall_score"], "Frontal crop must score higher than side crop"
    assert res_sharp["overall_score"] > res_non_face["overall_score"], "Verified face must score higher than non-face"
    assert "blurry" in res_blurry["flags"], "Blurry crop should have 'blurry' flag"
    assert "side_pose" in res_side["flags"], "Side crop should have 'side_pose' flag"
    assert "dim" in res_dark["flags"], "Dark crop should have 'dim' flag"
    assert res_dark["enhanced"] is True, "Dark crop should trigger CLAHE enhancement"
    assert "no_face" in res_non_face["flags"], "Non-face should have 'no_face' flag"
    assert res_non_face["overall_score"] <= 28.0, "Non-face score must be capped"

    print("\n[PASS] All Quality v2 tests successfully verified!")

if __name__ == "__main__":
    test_quality_ordering_and_flags()
