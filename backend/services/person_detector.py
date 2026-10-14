import os
from typing import List, Dict, Any, Optional
import numpy as np
import config

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from ultralytics import YOLO

class PersonDetector:
    """
    Person detection and multi-object tracking service utilizing YOLO.
    Configurable for CPU / GPU inference with explicit device assignment and ByteTrack tracking.
    """
    def __init__(
        self,
        model_name: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        imgsz: Optional[int] = None
    ):
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None
            else config.PERSON_CONFIDENCE_THRESHOLD
        )
        self.imgsz = imgsz if imgsz is not None else config.PERSON_IMGSZ
        self._fallback_counter = 1

        # Real GPU / accelerator detection
        self.cuda_available = False
        self.device = "cpu"
        if HAS_TORCH:
            if torch.cuda.is_available():
                self.cuda_available = True
                self.device = "cuda:0"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"

        chosen_model = model_name or config.PERSON_MODEL_NAME
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_weight = os.path.join(backend_dir, chosen_model)
        target_model = local_weight if os.path.exists(local_weight) else chosen_model

        try:
            self.model = YOLO(target_model)
            self.model_name = chosen_model
            print(f"[PersonDetector] Loaded {chosen_model} on device={self.device}")
        except Exception as e:
            print(f"[PersonDetector] Loading {target_model} failed ({e}), falling back to yolov8n.pt")
            self.model = YOLO("yolov8n.pt")
            self.model_name = "yolov8n.pt"

    def track(self, frame: np.ndarray, persist: bool = True) -> List[Dict[str, Any]]:
        """
        Processes a single frame, tracks detected persons, and returns bounding boxes with tracking IDs.
        """
        detections: List[Dict[str, Any]] = []
        if frame is None or frame.size == 0:
            return detections

        try:
            results = self.model.track(
                source=frame,
                persist=persist,
                classes=[0],  # COCO person class only
                conf=self.confidence_threshold,
                imgsz=self.imgsz,
                device=self.device,
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
        Prevents track ID collisions across sequential video uploads.
        """
        self._fallback_counter = 1
        try:
            if hasattr(self.model, "predictor") and self.model.predictor is not None:
                if hasattr(self.model.predictor, "trackers"):
                    for tracker in self.model.predictor.trackers:
                        if hasattr(tracker, "reset"):
                            tracker.reset()
                    self.model.predictor.trackers = []
            print("[PersonDetector] ByteTrack state successfully reset.")
        except Exception as e:
            print(f"[PersonDetector] reset_tracker warning: {e}")
