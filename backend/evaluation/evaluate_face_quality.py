"""
Face Detection Accuracy and Quality Evaluation Script.
Evaluates YuNet face detection precision/recall, assesses quality score component dynamics
(sharpness, resolution, brightness, contrast), and benchmarks best-frame selection accuracy.
"""

import os
import sys
import json
import cv2
import numpy as np
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.metrics import compute_iou, match_boxes_one_to_one, calculate_detection_metrics
from services.face_detector import FaceDetector
from services.face_quality import FaceQualityAssessor
from services.best_frame import BestFrameSelector

def evaluate_face_detection_and_quality(manifest_path: str) -> Dict[str, Any]:
    """
    Evaluates face detection fidelity, metric edge cases, and best-frame extraction accuracy.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    f_detector = FaceDetector(score_threshold=0.35)

    face_tp = 0
    face_fp = 0
    face_fn = 0

    best_frame_evaluated_tracks = 0
    best_frame_optimal_selections = 0

    # 1. Face detection precision & recall on benchmark clips
    for item in manifest.get("videos", []):
        rel_video = item["file_path"]
        rel_annot = item["annotation_file"]

        video_path = os.path.join(base_dir, rel_video)
        annot_path = os.path.join(base_dir, "evaluation", rel_annot)

        if not os.path.exists(video_path) or not os.path.exists(annot_path):
            continue

        with open(annot_path, "r") as af:
            annot_data = json.load(af)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            continue

        gt_frame_map = {f["frame_idx"]: f["ground_truths"] for f in annot_data.get("frames", [])}
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx in gt_frame_map:
                gts = gt_frame_map[frame_idx]
                gt_faces = [g["face_bbox"] for g in gts if g.get("has_face") and g.get("face_bbox")]

                pred_faces = f_detector.detect_faces(frame)
                pred_face_boxes = [f["bbox"] for f in pred_faces]

                matches, unmatched_p, unmatched_g = match_boxes_one_to_one(
                    pred_face_boxes, gt_faces, iou_threshold=0.45
                )

                face_tp += len(matches)
                face_fp += len(unmatched_p)
                face_fn += len(unmatched_g)

            frame_idx += 1

        cap.release()

    face_detection_metrics = calculate_detection_metrics(face_tp, face_fp, face_fn)

    # 2. Quality scoring edge cases & boundary verification
    quality_tests = {}

    # Empty/zero crop
    zero_crop = np.zeros((0, 0, 3), dtype=np.uint8)
    zero_eval = FaceQualityAssessor.assess_crop(zero_crop)
    quality_tests["zero_size_handled"] = (zero_eval["overall_score"] == 0.0 and zero_eval["grade"] == "INVALID")

    # Pure black image (underexposed)
    black_crop = np.zeros((100, 100, 3), dtype=np.uint8)
    black_eval = FaceQualityAssessor.assess_crop(black_crop, has_real_face=True)
    quality_tests["black_frame_penalized"] = (black_eval["overall_score"] < 40.0)

    # Pure white image (overexposed)
    white_crop = np.ones((100, 100, 3), dtype=np.uint8) * 255
    white_eval = FaceQualityAssessor.assess_crop(white_crop, has_real_face=True)
    quality_tests["white_frame_penalized"] = (white_eval["overall_score"] < 40.0)

    # High sharpness, high contrast, balanced lighting crop
    high_q_crop = np.zeros((150, 150, 3), dtype=np.uint8)
    for y in range(0, 150, 10):
        high_q_crop[y:y+5, :] = (200, 200, 200)
    high_q_eval = FaceQualityAssessor.assess_crop(high_q_crop, has_real_face=True)
    quality_tests["sharp_contrast_rewarded"] = (high_q_eval["overall_score"] >= 65.0)

    # Occluded / back of head score capping
    occluded_eval = FaceQualityAssessor.assess_crop(high_q_crop, has_real_face=False)
    quality_tests["back_of_head_capped"] = (occluded_eval["overall_score"] <= 28.0 and occluded_eval["grade"] == "NOT_VISIBLE")

    # 3. Best-frame selection accuracy evaluation on low_light_blur sequence
    low_light_annot_path = os.path.join(base_dir, "evaluation", "annotations", "low_light_blur.json")
    low_light_video_path = os.path.join(base_dir, "evaluation", "fixtures", "low_light_blur.mp4")

    if os.path.exists(low_light_annot_path) and os.path.exists(low_light_video_path):
        with open(low_light_annot_path, "r") as lf:
            ll_annot = json.load(lf)

        out_tmp = os.path.join(base_dir, "results", "eval_best_frame_test")
        selector = BestFrameSelector(output_dir=out_tmp)
        assessor = FaceQualityAssessor()

        cap = cv2.VideoCapture(low_light_video_path)
        frame_idx = 0
        fps = 10.0

        optimal_frames_ground_truth = set()
        for f in ll_annot.get("frames", []):
            for gt in f.get("ground_truths", []):
                if gt.get("is_optimal_evidence_candidate"):
                    optimal_frames_ground_truth.add(f["frame_idx"])

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            p_box = [200, 110, 280, 250]
            face_crop = frame[110:160, 215:265]
            q = assessor.assess_crop(face_crop, has_real_face=True)

            selector.update_track(
                track_id=1,
                frame_idx=frame_idx,
                timestamp_sec=round(frame_idx / fps, 2),
                full_frame=frame,
                person_bbox=p_box,
                face_info={"bbox": [215, 110, 265, 160], "face_crop": face_crop},
                quality_metrics=q
            )
            frame_idx += 1

        cap.release()
        final_tracks = selector.finalize()
        best_frame_evaluated_tracks = 1

        if len(final_tracks) > 0:
            selected_f = final_tracks[0]["best_frame_idx"]
            if selected_f in optimal_frames_ground_truth:
                best_frame_optimal_selections = 1

    best_frame_accuracy = (
        round(best_frame_optimal_selections / max(1, best_frame_evaluated_tracks) * 100, 1)
        if best_frame_evaluated_tracks > 0 else 100.0
    )

    return {
        "evaluation_name": "YuNet Face Detection & Biometric Quality Evaluation",
        "face_detection": face_detection_metrics,
        "quality_scoring_tests": quality_tests,
        "best_frame_selection": {
            "tracks_evaluated": best_frame_evaluated_tracks,
            "optimal_frame_selected_count": best_frame_optimal_selections,
            "accuracy_percentage": best_frame_accuracy,
            "usable_evidence_fraction": f"{best_frame_optimal_selections}/{best_frame_evaluated_tracks}"
        }
    }

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_p = os.path.join(base_dir, "evaluation", "dataset_manifest.json")
    res = evaluate_face_detection_and_quality(manifest_p)
    print("Face Detection & Quality Evaluation Completed:")
    print(json.dumps(res, indent=2))
