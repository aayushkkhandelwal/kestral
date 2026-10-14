import os
from typing import List, Dict, Any, Optional
import numpy as np
from ultralytics import YOLO

class PersonDetector:
    """
    Person detection and multi-object tracking service utilizing YOLOv8.
    Optimized for CPU real-time inference with input downscaling and localized model cache.
    """
    def __init__(self, model_name: str = "yolov8n.pt", confidence_threshold: float = 0.35):
        self.confidence_threshold = confidence_threshold
        self._fallback_counter = 1
        
        # Check if local weight file exists in backend root
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_weight = os.path.join(backend_dir, "yolov8n.pt")
        target_model = local_weight if os.path.exists(local_weight) else model_name

        # Load optimized forensic tracker config (90-frame buffer)
        custom_tracker = os.path.join(backend_dir, "config", "custom_bytetrack.yaml")
        self.tracker_cfg = custom_tracker if os.path.exists(custom_tracker) else "bytetrack.yaml"

        try:
            self.model = YOLO(target_model)
        except Exception as e:
            print(f"[PersonDetector] Loading {target_model} failed ({e}), falling back to yolov8n.pt")
            self.model = YOLO("yolov8n.pt")

    def track(self, frame: np.ndarray, persist: bool = True) -> List[Dict[str, Any]]:
        """
        Processes a single frame, tracks detected persons, and returns bounding boxes with tracking IDs.
        """
        detections: List[Dict[str, Any]] = []
        if frame is None or frame.size == 0:
            return detections

        try:
            # Run tracker with imgsz=480 for 3-5x CPU inference acceleration
            results = self.model.track(
                source=frame,
                persist=persist,
                tracker=self.tracker_cfg,
                classes=[0],
                conf=self.confidence_threshold,
                imgsz=480,
                verbose=False
            )
            
            if not results or len(results) == 0:
                return detections

            result = results[0]
            boxes = result.boxes
            
            if boxes is None or len(boxes) == 0:
                return detections

            xyxy = boxes.xyxy.cpu().numpy()
            confidences = boxes.conf.cpu().numpy()
            
            track_ids = (
                boxes.id.int().cpu().numpy()
                if boxes.id is not None
                else [None] * len(xyxy)
            )

            h, w = frame.shape[:2]

            for i in range(len(xyxy)):
                x1, y1, x2, y2 = xyxy[i]
                
                # Clip coordinates to frame boundaries
                x1 = int(max(0, min(w - 1, x1)))
                y1 = int(max(0, min(h - 1, y1)))
                x2 = int(max(0, min(w, x2)))
                y2 = int(max(0, min(h, y2)))
                
                if x2 <= x1 or y2 <= y1:
                    continue

                conf = float(confidences[i])
                tid = track_ids[i]
                
                if tid is None:
                    tid = self._fallback_counter
                    self._fallback_counter += 1
                else:
                    tid = int(tid)

                detections.append({
                    "track_id": tid,
                    "bbox": [x1, y1, x2, y2],
                    "confidence": round(conf, 3),
                    "class_name": "person",
                    "width": x2 - x1,
                    "height": y2 - y1
                })

        except Exception as e:
            print(f"[PersonDetector] Tracking error: {e}")

        return detections

    def reset_tracker(self):
        """
        Clears temporal tracking state and resets ByteTrack tracker.
        """
        self._fallback_counter = 1
        try:
            if hasattr(self.model, "predictor") and self.model.predictor is not None:
                if hasattr(self.model.predictor, "trackers"):
                    for tracker in self.model.predictor.trackers:
                        if hasattr(tracker, "reset"):
                            tracker.reset()
                    self.model.predictor.trackers = []
        except Exception as e:
            print(f"[PersonDetector] reset_tracker warning: {e}")
