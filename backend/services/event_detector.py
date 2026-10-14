"""
Kestral AI — Event Detection & Monitored Zone Spatial Reasoning.
Detects:
1. Person Entry (crossing boundary into monitored zone/polygon).
2. Person Exit (crossing boundary out of monitored zone/polygon).
3. Transaction Start / Inferred Transaction (sustained presence in ATM interaction area).
Includes robust debouncing, cooldown windows, and coordinate normalization.
"""

import time
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np


class EventDetector:
    """
    Spatial reasoning engine that tracks person positions relative to monitored zones
    and fires timestamped surveillance events.
    """

    def __init__(
        self,
        entry_exit_cooldown_sec: float = 4.0,
        dwell_transaction_threshold_sec: float = 4.0
    ):
        self.entry_exit_cooldown_sec = entry_exit_cooldown_sec
        self.dwell_transaction_threshold_sec = dwell_transaction_threshold_sec

        # State tracking: track_id -> { 'in_zone': bool, 'last_transition_time': float, 'entered_time': float, 'transaction_fired': bool }
        self.track_states: Dict[Tuple[str, int], Dict[str, Any]] = {}

    @staticmethod
    def is_point_in_polygon(point: Tuple[float, float], polygon_pts: List[List[float]]) -> bool:
        """
        Tests whether a 2D point (x, y) is inside a polygon using OpenCV pointPolygonTest.
        Points can be normalized [0, 1] or pixel coordinates.
        """
        if not polygon_pts or len(polygon_pts) < 3:
            return False
        contour = np.array(polygon_pts, dtype=np.float32)
        dist = cv2.pointPolygonTest(contour, point, False)
        return dist >= 0

    @staticmethod
    def get_track_anchor_point(bbox: List[int], frame_w: int, frame_h: int) -> Tuple[float, float]:
        """
        Returns the ground/feet anchor point of the person bounding box, normalized [0, 1].
        x = center, y = bottom (feet on ground).
        """
        x1, y1, x2, y2 = bbox
        cx = ((x1 + x2) / 2.0) / max(1.0, float(frame_w))
        bottom_y = float(y2) / max(1.0, float(frame_h))
        return (cx, bottom_y)

    def process_frame_tracks(
        self,
        frame_idx: int,
        timestamp_sec: float,
        detections: List[Dict[str, Any]],
        zones: List[Dict[str, Any]],
        frame_w: int,
        frame_h: int
    ) -> List[Dict[str, Any]]:
        """
        Evaluates active detections in the frame against all configured monitored zones.
        Returns a list of fired events:
        {
            'event_type': 'person_entry' | 'person_exit' | 'inferred_transaction',
            'video_timestamp_sec': float,
            'source_frame': int,
            'track_id': int,
            'zone_id': str,
            'zone_name': str,
            'confidence': float,
            'source': str,
            'metadata': dict
        }
        """
        fired_events: List[Dict[str, Any]] = []

        if not zones:
            # Default fallback ATM console zone if none configured (center-bottom interaction area)
            zones = [{
                "zone_id": "default_atm_zone",
                "name": "ATM Console Primary Zone",
                "zone_type": "polygon",
                "coordinates": [[0.05, 0.35], [0.95, 0.35], [0.95, 1.0], [0.05, 1.0]]
            }]

        active_track_ids = set()

        for det in detections:
            tid = int(det.get("track_id", 0))
            if tid <= 0:
                continue
            active_track_ids.add(tid)
            bbox = det.get("bbox", [0, 0, 0, 0])
            anchor = self.get_track_anchor_point(bbox, frame_w, frame_h)

            for zone in zones:
                zone_id = str(zone.get("zone_id", "default"))
                zone_name = zone.get("name", "Monitored Zone")
                coords = zone.get("coordinates", [])

                # Convert coordinates to normalized if they are absolute
                norm_coords = []
                for pt in coords:
                    px, py = pt[0], pt[1]
                    if px > 1.0:
                        px = px / max(1.0, float(frame_w))
                    if py > 1.0:
                        py = py / max(1.0, float(frame_h))
                    norm_coords.append([px, py])

                inside = self.is_point_in_polygon(anchor, norm_coords)
                state_key = (zone_id, tid)

                if state_key not in self.track_states:
                    self.track_states[state_key] = {
                        "in_zone": inside,
                        "last_transition_time": timestamp_sec if inside else -999.0,
                        "entered_time": timestamp_sec if inside else 0.0,
                        "transaction_fired": False
                    }
                    if inside:
                        # Initial Entry Event
                        fired_events.append({
                            "event_type": "person_entry",
                            "video_timestamp_sec": timestamp_sec,
                            "source_frame": frame_idx,
                            "person_number": tid,
                            "zone_id": zone_id if zone_id != "default_atm_zone" else None,
                            "zone_name": zone_name,
                            "confidence": float(det.get("confidence", 0.9)),
                            "source": "vision_analytics",
                            "metadata": {
                                "bbox": bbox,
                                "anchor": anchor,
                                "reason": "Initial detection inside monitored zone"
                            }
                        })
                else:
                    st = self.track_states[state_key]
                    prev_inside = st["in_zone"]

                    # 1. Entry Transition
                    if not prev_inside and inside:
                        if (timestamp_sec - st["last_transition_time"]) >= self.entry_exit_cooldown_sec:
                            st["in_zone"] = True
                            st["last_transition_time"] = timestamp_sec
                            st["entered_time"] = timestamp_sec
                            st["transaction_fired"] = False
                            fired_events.append({
                                "event_type": "person_entry",
                                "video_timestamp_sec": timestamp_sec,
                                "source_frame": frame_idx,
                                "person_number": tid,
                                "zone_id": zone_id if zone_id != "default_atm_zone" else None,
                                "zone_name": zone_name,
                                "confidence": float(det.get("confidence", 0.9)),
                                "source": "vision_analytics",
                                "metadata": {
                                    "bbox": bbox,
                                    "anchor": anchor,
                                    "reason": "Boundary crossing into zone"
                                }
                            })

                    # 2. Exit Transition
                    elif prev_inside and not inside:
                        if (timestamp_sec - st["last_transition_time"]) >= self.entry_exit_cooldown_sec:
                            st["in_zone"] = False
                            st["last_transition_time"] = timestamp_sec
                            dwell_duration = round(timestamp_sec - st.get("entered_time", timestamp_sec), 2)
                            fired_events.append({
                                "event_type": "person_exit",
                                "video_timestamp_sec": timestamp_sec,
                                "source_frame": frame_idx,
                                "person_number": tid,
                                "zone_id": zone_id if zone_id != "default_atm_zone" else None,
                                "zone_name": zone_name,
                                "confidence": float(det.get("confidence", 0.9)),
                                "source": "vision_analytics",
                                "metadata": {
                                    "bbox": bbox,
                                    "anchor": anchor,
                                    "dwell_duration_sec": dwell_duration,
                                    "reason": "Boundary crossing out of zone"
                                }
                            })

                    # 3. Inferred Transaction Start (Sustained dwell at ATM console)
                    elif inside and not st["transaction_fired"]:
                        dwell_time = timestamp_sec - st["entered_time"]
                        if dwell_time >= self.dwell_transaction_threshold_sec:
                            st["transaction_fired"] = True
                            fired_events.append({
                                "event_type": "transaction_start",
                                "video_timestamp_sec": timestamp_sec,
                                "source_frame": frame_idx,
                                "person_number": tid,
                                "zone_id": zone_id if zone_id != "default_atm_zone" else None,
                                "zone_name": zone_name,
                                "confidence": 0.85,
                                "source": "inferred_rule",
                                "metadata": {
                                    "bbox": bbox,
                                    "dwell_before_start_sec": round(dwell_time, 2),
                                    "reason": "Sustained customer presence at ATM interface"
                                }
                            })

        return fired_events
