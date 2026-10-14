"""
Evaluation metrics for detection, tracking, face detection, and forensic evidence integrity.
Provides reproducible calculation of IoU, one-to-one box matching, Precision, Recall, F1,
mAP@0.50, MOT metrics (ID switches, fragmentation), and SHA-256 verification.
"""

import hashlib
import os
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    """
    Computes Intersection-over-Union (IoU) between two bounding boxes [x1, y1, x2, y2].
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interWidth = max(0.0, xB - xA)
    interHeight = max(0.0, yB - yA)
    interArea = interWidth * interHeight

    boxAArea = max(0.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(0.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    unionArea = boxAArea + boxBArea - interArea
    if unionArea <= 0.0:
        return 0.0

    return float(interArea / unionArea)

def match_boxes_one_to_one(
    pred_boxes: List[List[float]],
    gt_boxes: List[List[float]],
    iou_threshold: float = 0.50
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Greedy one-to-one matching between predictions and ground truths sorted by highest IoU.
    Ensures a single prediction cannot match multiple ground truth boxes and vice versa.
    Returns:
        - matches: list of (pred_idx, gt_idx)
        - unmatched_preds: list of pred_idx (False Positives)
        - unmatched_gts: list of gt_idx (False Negatives)
    """
    if len(pred_boxes) == 0:
        return [], [], list(range(len(gt_boxes)))
    if len(gt_boxes) == 0:
        return [], list(range(len(pred_boxes))), []

    candidates = []
    for p_idx, p_box in enumerate(pred_boxes):
        for g_idx, g_box in enumerate(gt_boxes):
            iou = compute_iou(p_box, g_box)
            if iou >= iou_threshold:
                candidates.append((iou, p_idx, g_idx))

    # Sort candidates descending by IoU
    candidates.sort(key=lambda x: x[0], reverse=True)

    matched_p = set()
    matched_g = set()
    matches = []

    for iou, p_idx, g_idx in candidates:
        if p_idx not in matched_p and g_idx not in matched_g:
            matched_p.add(p_idx)
            matched_g.add(g_idx)
            matches.append((p_idx, g_idx))

    unmatched_preds = [i for i in range(len(pred_boxes)) if i not in matched_p]
    unmatched_gts = [i for i in range(len(gt_boxes)) if i not in matched_g]

    return matches, unmatched_preds, unmatched_gts

def calculate_detection_metrics(
    true_positives: int,
    false_positives: int,
    false_negatives: int
) -> Dict[str, float]:
    """
    Calculates Precision, Recall, and F1-score from TP, FP, FN counts.
    """
    precision = float(true_positives / (true_positives + false_positives)) if (true_positives + false_positives) > 0 else 0.0
    recall = float(true_positives / (true_positives + false_negatives)) if (true_positives + false_negatives) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }

def calculate_map50(
    predictions_with_conf: List[Dict[str, Any]],
    total_ground_truths: int,
    iou_threshold: float = 0.50
) -> float:
    """
    Calculates Average Precision at IoU 0.50 (AP@0.50) using the 11-point interpolation or area under PR curve.
    predictions_with_conf: list of dicts with:
        - 'confidence': float
        - 'is_tp': bool (from one-to-one match)
    """
    if total_ground_truths <= 0:
        return 1.0 if len(predictions_with_conf) == 0 else 0.0
    if len(predictions_with_conf) == 0:
        return 0.0

    # Sort descending by confidence
    sorted_preds = sorted(predictions_with_conf, key=lambda x: x["confidence"], reverse=True)

    tp_cumsum = 0
    fp_cumsum = 0
    precisions = []
    recalls = []

    for item in sorted_preds:
        if item["is_tp"]:
            tp_cumsum += 1
        else:
            fp_cumsum += 1

        p = tp_cumsum / (tp_cumsum + fp_cumsum)
        r = tp_cumsum / total_ground_truths
        precisions.append(p)
        recalls.append(r)

    # Compute area under curve using standard VOC/COCO trapezoid approximation
    recalls = [0.0] + recalls + [1.0]
    precisions = [0.0] + precisions + [0.0]

    # Make precision monotonically decreasing
    for i in range(len(precisions) - 2, -1, -1):
        precisions[i] = max(precisions[i], precisions[i + 1])

    # Integrate area under curve where recall changes
    ap = 0.0
    for i in range(1, len(recalls)):
        if recalls[i] != recalls[i - 1]:
            ap += (recalls[i] - recalls[i - 1]) * precisions[i]

    return round(float(ap), 4)

def compute_tracking_metrics(
    gt_tracks: Dict[int, List[Dict[str, Any]]],
    pred_tracks: Dict[int, List[Dict[str, Any]]],
    iou_threshold: float = 0.50
) -> Dict[str, Any]:
    """
    Computes tracking consistency metrics:
    - ID Switches: When a ground truth person is tracked, but the predicted tracker ID changes.
    - Track Fragmentation: When tracking is interrupted and resumes with a gap.
    - Track Duration: Average duration of continuous tracks.
    """
    id_switches = 0
    fragmentations = 0
    gt_to_pred_map: Dict[int, int] = {}
    gt_last_frame: Dict[int, int] = {}

    # Build per-frame index: frame_idx -> list of (gt_id, bbox)
    frames_gt: Dict[int, List[Tuple[int, List[float]]]] = {}
    for gid, detections in gt_tracks.items():
        for d in detections:
            f_idx = d["frame_idx"]
            frames_gt.setdefault(f_idx, []).append((gid, d["bbox"]))

    frames_pred: Dict[int, List[Tuple[int, List[float]]]] = {}
    for pid, detections in pred_tracks.items():
        for d in detections:
            f_idx = d["frame_idx"]
            frames_pred.setdefault(f_idx, []).append((pid, d["bbox"]))

    all_frame_indices = sorted(set(list(frames_gt.keys()) + list(frames_pred.keys())))

    for f_idx in all_frame_indices:
        gts = frames_gt.get(f_idx, [])
        preds = frames_pred.get(f_idx, [])

        p_boxes = [p[1] for p in preds]
        g_boxes = [g[1] for g in gts]

        matches, _, _ = match_boxes_one_to_one(p_boxes, g_boxes, iou_threshold=iou_threshold)

        for p_i, g_i in matches:
            pred_id = preds[p_i][0]
            gt_id = gts[g_i][0]

            if gt_id in gt_to_pred_map:
                prev_pred_id = gt_to_pred_map[gt_id]
                if prev_pred_id != pred_id:
                    id_switches += 1
                    gt_to_pred_map[gt_id] = pred_id
            else:
                gt_to_pred_map[gt_id] = pred_id

            # Check fragmentation (interruption > 1 frame)
            if gt_id in gt_last_frame:
                if f_idx - gt_last_frame[gt_id] > 1:
                    fragmentations += 1
            gt_last_frame[gt_id] = f_idx

    total_gt_identities = len(gt_tracks)
    total_pred_tracks = len(pred_tracks)

    return {
        "ground_truth_identities": total_gt_identities,
        "predicted_tracks": total_pred_tracks,
        "id_switches": id_switches,
        "track_fragmentations": fragmentations,
        "switch_rate_per_identity": round(id_switches / max(1, total_gt_identities), 3)
    }

def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 hash of a file on disk."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot hash non-existent file: {filepath}")
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def verify_file_integrity(filepath: str, expected_hash: str) -> Dict[str, Any]:
    """
    Compares recorded hash against live calculated file hash.
    Returns status: 'MATCH', 'MODIFIED', or 'MISSING'.
    """
    if not os.path.exists(filepath):
        return {
            "status": "MISSING",
            "file": filepath,
            "expected_hash": expected_hash,
            "calculated_hash": None,
            "is_valid": False
        }
    actual_hash = compute_sha256(filepath)
    is_match = (actual_hash.lower() == expected_hash.lower())
    return {
        "status": "MATCH" if is_match else "MODIFIED",
        "file": filepath,
        "expected_hash": expected_hash,
        "calculated_hash": actual_hash,
        "is_valid": is_match
    }
