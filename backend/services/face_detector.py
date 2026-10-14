import os
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np

class FaceDetector:
    """
    Face detection service that locates faces within full frames or localized person bounding box crops.
    Employs OpenCV Haar cascade classifiers with fallback head/upper-body heuristics.
    """
    def __init__(self, min_face_size: Tuple[int, int] = (30, 30)):
        self.min_face_size = min_face_size
        
        # Load frontal and profile face cascades from standard OpenCV package
        cascade_dir = cv2.data.haarcascades
        self.frontal_cascade = cv2.CascadeClassifier(
            os.path.join(cascade_dir, "haarcascade_frontalface_default.xml")
        )
        self.profile_cascade = cv2.CascadeClassifier(
            os.path.join(cascade_dir, "haarcascade_profileface.xml")
        )

    def detect_face_in_person(
        self, frame: np.ndarray, person_bbox: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Locates the best face candidate within a detected person's bounding box.
        
        Args:
            frame: Full BGR frame
            person_bbox: [x1, y1, x2, y2] of the person
            
        Returns:
            Dict containing:
              - 'bbox': [fx1, fy1, fx2, fy2] relative to full frame
              - 'face_crop': cropped numpy image of the face
              - 'is_heuristic': bool (True if inferred head crop was used as fallback)
              - 'confidence': estimated detection confidence
        """
        if frame is None or frame.size == 0:
            return None

        h, w = frame.shape[:2]
        px1, py1, px2, py2 = person_bbox
        px1, py1 = max(0, px1), max(0, py1)
        px2, py2 = min(w, px2), min(h, py2)

        p_width = px2 - px1
        p_height = py2 - py1

        if p_width < 20 or p_height < 30:
            return None

        # Focus face search primarily on the upper 55% of the person's bounding box
        head_region_h = int(p_height * 0.55)
        crop_y2 = min(h, py1 + head_region_h)
        person_upper_crop = frame[py1:crop_y2, px1:px2]

        if person_upper_crop.size == 0:
            return None

        gray_upper = cv2.cvtColor(person_upper_crop, cv2.COLOR_BGR2GRAY)
        gray_upper = cv2.equalizeHist(gray_upper)

        # 1. Try frontal face detection
        faces = self.frontal_cascade.detectMultiScale(
            gray_upper,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=self.min_face_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # 2. If no frontal face, try profile face detection
        if len(faces) == 0:
            faces = self.profile_cascade.detectMultiScale(
                gray_upper,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=self.min_face_size
            )

        if len(faces) > 0:
            # Pick largest detected face
            best_face = max(faces, key=lambda f: f[2] * f[3])
            fx, fy, fw, fh = best_face

            # Map coordinates back to full frame
            abs_x1 = max(0, px1 + fx)
            abs_y1 = max(0, py1 + fy)
            abs_x2 = min(w, abs_x1 + fw)
            abs_y2 = min(h, abs_y1 + fh)

            # Add subtle margin (10%) for better visual evidence
            pad_x = int(fw * 0.1)
            pad_y = int(fh * 0.1)
            abs_x1 = max(0, abs_x1 - pad_x)
            abs_y1 = max(0, abs_y1 - pad_y)
            abs_x2 = min(w, abs_x2 + pad_x)
            abs_y2 = min(h, abs_y2 + pad_y)

            face_crop = frame[abs_y1:abs_y2, abs_x1:abs_x2]
            if face_crop.size > 0:
                return {
                    "bbox": [abs_x1, abs_y1, abs_x2, abs_y2],
                    "face_crop": face_crop,
                    "is_heuristic": False,
                    "confidence": 0.92
                }

        # 3. Fallback Heuristic: Estimate upper 30% center region as head/face
        head_top = py1
        head_bottom = min(h, py1 + int(p_height * 0.32))
        center_x = px1 + p_width // 2
        half_head_w = int(p_width * 0.28)
        head_left = max(0, center_x - half_head_w)
        head_right = min(w, center_x + half_head_w)

        head_crop = frame[head_top:head_bottom, head_left:head_right]
        if head_crop.size > 0 and (head_right - head_left) > 15 and (head_bottom - head_top) > 15:
            return {
                "bbox": [head_left, head_top, head_right, head_bottom],
                "face_crop": head_crop,
                "is_heuristic": True,
                "confidence": 0.50
            }

        return None
