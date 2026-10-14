import os
from typing import List, Dict, Any, Optional
import numpy as np
from ultralytics import YOLO

class PersonDetector:
    """
    Person detection and multi-object tracking service utilizing YOLOv8/v11.
    Filters specifically for person classes (COCO class 0) and tracks subjects across frames.
    """
    def __init__(self, model_name: str = "yolov8n.pt", confidence_threshold: float = 0.35):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self._fallback_counter = 1
        
        # Initialize YOLO model
        try:
            self.model = YOLO(model_name)
        except Exception as e:
            print(f"[PersonDetector] Warning: Could not initialize {model_name} directly ({e}). Attempting default load.")
            self.model = YOLO("yolov8n.pt")

    def track(self, frame: np.ndarray, persist: bool = True) -> List[Dict[str, Any]]:
        """
        Processes a single frame, tracks detected persons, and returns bounding boxes with tracking IDs.
        
        Args:
            frame: BGR numpy image frame
            persist: Keep track history for multi-object tracking
            
        Returns:
            List of detected persons with bounding boxes, confidence, and track_id
        """
        detections: List[Dict[str, Any]] = []
        if frame is None or frame.size == 0:
            return detections

        try:
            # Run tracker specifically for class 0 (person)
            results = self.model.track(
                source=frame,
                persist=persist,
                classes=[0],
                conf=self.confidence_threshold,
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
            
            # Track IDs may be None if tracker hasn't assigned them yet
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
                    # Provide an ephemeral fallback ID
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
            print(f"[PersonDetector] Tracking error on frame: {e}")

        return detections
