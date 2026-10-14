import os
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np

class FaceDetector:
    """
    Biometric face and head localization service.
    Extracts facial evidence from tracked subjects using Haar cascades when available,
    with an optimized anatomical head/facial ROI extractor fallback.
    """
    def __init__(self, min_face_size: Tuple[int, int] = (30, 30)):
        self.min_face_size = min_face_size
        self.has_cascades = False
        
        # Safely attempt to initialize Haar cascade if available in OpenCV build
        try:
            if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
                cascade_dir = cv2.data.haarcascades
                frontal_path = os.path.join(cascade_dir, "haarcascade_frontalface_default.xml")
                if os.path.exists(frontal_path):
                    self.frontal_cascade = cv2.CascadeClassifier(frontal_path)
                    self.has_cascades = not self.frontal_cascade.empty()
        except Exception:
            self.has_cascades = False

    def detect_face_in_person(
        self, frame: np.ndarray, person_bbox: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Locates the best face candidate within a detected person's bounding box.
        """
        if frame is None or frame.size == 0:
            return None

        h, w = frame.shape[:2]
        px1, py1, px2, py2 = person_bbox
        px1, py1 = max(0, px1), max(0, py1)
        px2, py2 = min(w, px2), min(h, py2)

        p_width = px2 - px1
        p_height = py2 - py1

        if p_width < 15 or p_height < 25:
            return None

        # 1. If cascades are available, try frontal face detection on upper body
        if self.has_cascades:
            try:
                head_region_h = int(p_height * 0.50)
                crop_y2 = min(h, py1 + head_region_h)
                person_upper = frame[py1:crop_y2, px1:px2]

                if person_upper.size > 0:
                    gray = cv2.cvtColor(person_upper, cv2.COLOR_BGR2GRAY)
                    faces = self.frontal_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=4,
                        minSize=self.min_face_size
                    )
                    if len(faces) > 0:
                        best = max(faces, key=lambda f: f[2] * f[3])
                        fx, fy, fw, fh = best
                        abs_x1 = max(0, px1 + fx - int(fw * 0.1))
                        abs_y1 = max(0, py1 + fy - int(fh * 0.1))
                        abs_x2 = min(w, abs_x1 + int(fw * 1.2))
                        abs_y2 = min(h, abs_y1 + int(fh * 1.2))
                        crop = frame[abs_y1:abs_y2, abs_x1:abs_x2]
                        if crop.size > 0:
                            return {
                                "bbox": [abs_x1, abs_y1, abs_x2, abs_y2],
                                "face_crop": crop,
                                "is_heuristic": False,
                                "confidence": 0.95
                            }
            except Exception:
                pass

        # 2. Optimized Anatomical Facial ROI: Upper 33% center region of tracked person
        head_top = py1
        head_bottom = min(h, py1 + int(p_height * 0.35))
        center_x = px1 + p_width // 2
        half_head_w = int(p_width * 0.32)
        head_left = max(0, center_x - half_head_w)
        head_right = min(w, center_x + half_head_w)

        head_crop = frame[head_top:head_bottom, head_left:head_right]
        if head_crop.size > 0 and (head_right - head_left) > 10 and (head_bottom - head_top) > 10:
            return {
                "bbox": [head_left, head_top, head_right, head_bottom],
                "face_crop": head_crop,
                "is_heuristic": True,
                "confidence": 0.85
            }

        return None
