"""
Tracking Stability Evaluation Script.
Evaluates ByteTrack tracking consistency across multi-person crossings, occlusions, and disappearances.
Measures ID switches, track fragmentation, and track duration continuity.
"""

import os
import sys
import json
import cv2
from typing import Dict, Any, List
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.metrics import compute_tracking_metrics
from services.person_detector import PersonDetector

def evaluate_tracking(manifest_path: str, iou_thresh: float = 0.50) -> Dict[str, Any]:
    """
    Evaluates tracking continuity across all annotated benchmark sequences.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    detector = PersonDetector(confidence_threshold=0.35)

    tracking_results = []
    total_gt_ids = 0
    total_pred_ids = 0
    total_id_switches = 0
    total_fragmentations = 0

    for item in manifest.get("videos", []):
        if item.get("category") != "tracking_benchmark":
            continue

        rel_video = item["file_path"]
        rel_annot = item["annotation_file"]

        video_path = os.path.join(base_dir, rel_video)
        annot_path = os.path.join(base_dir, "evaluation", rel_annot)

        if not os.path.exists(video_path) or not os.path.exists(annot_path):
            continue

        with open(annot_path, "r") as af:
            annot_data = json.load(af)

        detector.reset_tracker()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            continue

        # Parse ground-truth tracks
        gt_tracks: Dict[int, List[Dict[str, Any]]] = {}
        for f in annot_data.get("frames", []):
            f_idx = f["frame_idx"]
            for gt in f.get("ground_truths", []):
                tid = gt["track_id"]
                gt_tracks.setdefault(tid, []).append({
                    "frame_idx": f_idx,
                    "bbox": gt["bbox"]
                })

        # Run tracking inference
        pred_tracks: Dict[int, List[Dict[str, Any]]] = {}
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            detections = detector.track(frame, persist=True)
            for d in detections:
                pid = d["track_id"]
                pred_tracks.setdefault(pid, []).append({
                    "frame_idx": frame_idx,
                    "bbox": d["bbox"]
                })

            frame_idx += 1

        cap.release()

        metrics = compute_tracking_metrics(gt_tracks, pred_tracks, iou_threshold=iou_thresh)
        metrics["video_id"] = item["video_id"]
        metrics["test_condition"] = item["test_condition"]
        metrics["frames_evaluated"] = frame_idx

        tracking_results.append(metrics)
        total_gt_ids += metrics["ground_truth_identities"]
        total_pred_ids += metrics["predicted_tracks"]
        total_id_switches += metrics["id_switches"]
        total_fragmentations += metrics["track_fragmentations"]

    overall_tracking = {
        "total_gt_identities": total_gt_ids,
        "total_predicted_tracks": total_pred_ids,
        "total_id_switches": total_id_switches,
        "total_fragmentations": total_fragmentations,
        "switch_rate_per_identity": round(total_id_switches / max(1, total_gt_ids), 3),
        "fragmentation_rate": round(total_fragmentations / max(1, total_gt_ids), 3)
    }

    return {
        "evaluation_name": "ByteTrack Tracking Stability Evaluation",
        "iou_threshold": iou_thresh,
        "overall": overall_tracking,
        "per_sequence": tracking_results
    }

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_p = os.path.join(base_dir, "evaluation", "dataset_manifest.json")
    res = evaluate_tracking(manifest_p)
    print("Tracking Stability Evaluation Completed:")
    print(json.dumps(res["overall"], indent=2))
