"""
Transaction Linking Engine for Kestral
Associates ATM cash withdrawal transactions with tracked individuals based on
spatiotemporal dwell analysis in the designated ATM interaction zone.
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import cv2
from config import LINKING_TIME_PADDING_SEC, LINKING_CONFIDENCE_THRESHOLD, LINKING_CLOSE_MARGIN

def is_point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
    """
    Checks if a point (x, y) is inside the ROI polygon using cv2.pointPolygonTest.
    """
    if not polygon or len(polygon) < 3:
        return False
    poly_np = np.array(polygon, dtype=np.float32)
    dist = cv2.pointPolygonTest(poly_np, (float(point[0]), float(point[1])), measureDist=False)
    return dist >= 0.0

def compute_transaction_link(
    txn_id: str,
    task_id: str,
    start_s: float,
    end_s: float,
    tracks: List[Dict[str, Any]],
    roi_polygon: Optional[List[List[float]]] = None,
    pad_s: float = LINKING_TIME_PADDING_SEC,
    confidence_thresh: float = LINKING_CONFIDENCE_THRESHOLD,
    close_margin: float = LINKING_CLOSE_MARGIN
) -> Dict[str, Any]:
    """
    Evaluates all tracks against the transaction time window [start_s - pad, end_s + pad]
    and the ATM ROI polygon.

    Returns:
        LinkResult:
        {
            "txn_id": txn_id,
            "task_id": task_id,
            "track_id": int | None,
            "confidence": float (0.0 to 1.0),
            "ambiguous": bool,
            "candidates": [{"track_id": int, "dwell_s": float}]
        }
    """
    window_start = max(0.0, start_s - pad_s)
    window_end = end_s + pad_s
    dwell_per_track: Dict[int, float] = {}

    for track in tracks:
        tid = track.get("track_id")
        trajectory = track.get("trajectory", [])
        if tid is None or not trajectory:
            continue

        # Sort trajectory by timestamp
        sorted_traj = sorted(trajectory, key=lambda p: p[0])
        total_dwell = 0.0

        for i, point in enumerate(sorted_traj):
            t, x1, y1, x2, y2 = point[:5]
            if not (window_start <= t <= window_end):
                continue

            # Bottom-center of bounding box represents feet position on the floor
            feet_x = (x1 + x2) / 2.0
            feet_y = float(y2)

            in_zone = True
            if roi_polygon and len(roi_polygon) >= 3:
                in_zone = is_point_in_polygon((feet_x, feet_y), roi_polygon)

            if in_zone:
                # Estimate time slice represented by this sample
                if i < len(sorted_traj) - 1:
                    dt = max(0.0, min(1.0, sorted_traj[i + 1][0] - t))
                elif i > 0:
                    dt = max(0.0, min(1.0, t - sorted_traj[i - 1][0]))
                else:
                    dt = 0.15  # Fallback duration per frame
                total_dwell += dt

        if total_dwell > 0.0:
            dwell_per_track[tid] = round(total_dwell, 2)

    if not dwell_per_track:
        return {
            "txn_id": txn_id,
            "task_id": task_id,
            "track_id": None,
            "confidence": 0.0,
            "ambiguous": False,
            "candidates": []
        }

    # Sort candidates by dwell time descending
    sorted_candidates = sorted(
        [{"track_id": tid, "dwell_s": dwell} for tid, dwell in dwell_per_track.items()],
        key=lambda c: c["dwell_s"],
        reverse=True
    )

    total_dwell_sum = sum(c["dwell_s"] for c in sorted_candidates)
    best_candidate = sorted_candidates[0]
    best_dwell = best_candidate["dwell_s"]

    # Calculate confidence as ratio of best dwell to total dwell
    confidence = round(best_dwell / total_dwell_sum, 2) if total_dwell_sum > 0 else 0.0

    # Ambiguity checks:
    # 1. Low overall confidence
    # 2. Or runner-up dwell is within close_margin of best dwell (e.g. queue or handoff)
    is_ambiguous = False
    if confidence < confidence_thresh:
        is_ambiguous = True
    elif len(sorted_candidates) > 1:
        second_dwell = sorted_candidates[1]["dwell_s"]
        ratio_diff = (best_dwell - second_dwell) / max(0.001, total_dwell_sum)
        if ratio_diff < close_margin:
            is_ambiguous = True

    return {
        "txn_id": txn_id,
        "task_id": task_id,
        "track_id": best_candidate["track_id"],
        "confidence": confidence,
        "ambiguous": is_ambiguous,
        "candidates": sorted_candidates
    }
