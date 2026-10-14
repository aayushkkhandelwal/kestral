"""
Person Detection Accuracy Evaluation Script.
Evaluates the YOLOv8n detector against ground-truth bounding box annotations.
Calculates Precision, Recall, F1, TP, FP, FN, and mAP@0.50 with per-condition breakdown.
"""

import os
import sys
import json
import cv2
from typing import Dict, Any, List
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.metrics import compute_iou, match_boxes_one_to_one, calculate_detection_metrics, calculate_map50
from services.person_detector import PersonDetector

def evaluate_detection(
    manifest_path: str,
    iou_thresh: float = 0.50,
    conf_thresh: float = 0.35
) -> Dict[str, Any]:
    """
    Runs person detection evaluation across all manifest entries with ground truth annotations.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    detector = PersonDetector(confidence_threshold=conf_thresh)

    overall_tp = 0
    overall_fp = 0
    overall_fn = 0
    all_preds_for_map = []
    total_gts_overall = 0

    per_condition_metrics = {}
    video_results = []

    for item in manifest.get("videos", []):
        rel_video = item["file_path"]
        rel_annot = item["annotation_file"]
        condition = item["test_condition"]

        video_path = os.path.join(base_dir, rel_video)
        annot_path = os.path.join(base_dir, "evaluation", rel_annot)

        if not os.path.exists(video_path) or not os.path.exists(annot_path):
            continue

        with open(annot_path, "r") as af:
            annot_data = json.load(af)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            continue

        # Map frames by frame_idx
        gt_frame_map = {f["frame_idx"]: f["ground_truths"] for f in annot_data.get("frames", [])}

        vid_tp = 0
        vid_fp = 0
        vid_fn = 0
        vid_preds_map = []
        vid_gts_count = 0

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx in gt_frame_map:
                gts = gt_frame_map[frame_idx]
                gt_boxes = [g["bbox"] for g in gts]
                vid_gts_count += len(gt_boxes)
                total_gts_overall += len(gt_boxes)

                # Run detector
                detections = detector.track(frame, persist=True)
                pred_boxes = [d["bbox"] for d in detections]
                confidences = [d.get("confidence", 1.0) for d in detections]

                matches, unmatched_p, unmatched_g = match_boxes_one_to_one(
                    pred_boxes, gt_boxes, iou_threshold=iou_thresh
                )

                vid_tp += len(matches)
                vid_fp += len(unmatched_p)
                vid_fn += len(unmatched_g)

                matched_p_indices = {m[0] for m in matches}
                for p_idx, conf in enumerate(confidences):
                    is_tp = (p_idx in matched_p_indices)
                    item_pred = {"confidence": conf, "is_tp": is_tp}
                    vid_preds_map.append(item_pred)
                    all_preds_for_map.append(item_pred)

            frame_idx += 1

        cap.release()

        overall_tp += vid_tp
        overall_fp += vid_fp
        overall_fn += vid_fn

        vid_metrics = calculate_detection_metrics(vid_tp, vid_fp, vid_fn)
        vid_map = calculate_map50(vid_preds_map, vid_gts_count, iou_threshold=iou_thresh)
        vid_metrics["mAP50"] = vid_map
        vid_metrics["video_id"] = item["video_id"]
        vid_metrics["condition"] = condition
        video_results.append(vid_metrics)

        # Aggregate per-condition
        if condition not in per_condition_metrics:
            per_condition_metrics[condition] = {"tp": 0, "fp": 0, "fn": 0, "preds": [], "gts": 0}
        cond = per_condition_metrics[condition]
        cond["tp"] += vid_tp
        cond["fp"] += vid_fp
        cond["fn"] += vid_fn
        cond["preds"].extend(vid_preds_map)
        cond["gts"] += vid_gts_count

    # Compile condition metrics
    condition_summary = {}
    for c_name, c_data in per_condition_metrics.items():
        c_met = calculate_detection_metrics(c_data["tp"], c_data["fp"], c_data["fn"])
        c_met["mAP50"] = calculate_map50(c_data["preds"], c_data["gts"], iou_threshold=iou_thresh)
        condition_summary[c_name] = c_met

    overall_metrics = calculate_detection_metrics(overall_tp, overall_fp, overall_fn)
    overall_map50 = calculate_map50(all_preds_for_map, total_gts_overall, iou_threshold=iou_thresh)
    overall_metrics["mAP50"] = overall_map50

    return {
        "evaluation_name": "YOLOv8n Person Detection Evaluation",
        "iou_threshold": iou_thresh,
        "confidence_threshold": conf_thresh,
        "overall": overall_metrics,
        "per_condition": condition_summary,
        "per_video": video_results
    }

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_p = os.path.join(base_dir, "evaluation", "dataset_manifest.json")
    results = evaluate_detection(manifest_p)
    print("Person Detection Evaluation Completed:")
    print(json.dumps(results["overall"], indent=2))
