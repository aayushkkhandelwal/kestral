import os
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np

class FaceDetector:
    """
    High-accuracy facial recognition & orientation detector utilizing OpenCV YuNet DNN.
    Accurately detects whether a real face (eyes, nose, mouth) is visible towards the camera,
    distinguishing true facial captures from back-of-head / turned-away views.
    """
    def __init__(self, score_threshold: float = 0.55):
        self.score_threshold = score_threshold
        self.yunet = None
        
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(backend_dir, "models", "face_detection_yunet.onnx")
        
        if os.path.exists(model_path) and hasattr(cv2, 'FaceDetectorYN_create'):
            try:
                self.yunet = cv2.FaceDetectorYN_create(
                    model_path,
                    "",
                    (320, 320),
                    score_threshold=self.score_threshold,
                    nms_threshold=0.3
                )
            except Exception as e:
                print(f"[FaceDetector] Warning: YuNet init failed ({e})")

    def detect_face_in_person(
        self, frame: np.ndarray, person_bbox: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Locates the face within a person's upper body.
        Returns:
            - 'bbox': [fx1, fy1, fx2, fy2]
            - 'face_crop': cropped image
            - 'has_real_face': True if eyes/nose/mouth were verified by neural network
            - 'confidence': confidence score (0.0 to 1.0)
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

        # Focus face search on upper 60% of person (head, face, neck)
        head_region_h = int(p_height * 0.60)
        crop_y2 = min(h, py1 + head_region_h)
        upper_crop = frame[py1:crop_y2, px1:px2]

        if upper_crop.size == 0:
            return None

        uh, uw = upper_crop.shape[:2]

        # 1. Try Deep Face Detector (YuNet)
        if self.yunet is not None and uw >= 20 and uh >= 20:
            try:
                # Downsample large crops for rapid inference
                max_dim = max(uw, uh)
                scale = 320.0 / max_dim if max_dim > 320 else 1.0
                if scale < 1.0:
                    net_w = int(uw * scale)
                    net_h = int(uh * scale)
                    input_img = cv2.resize(upper_crop, (net_w, net_h))
                else:
                    net_w, net_h = uw, uh
                    input_img = upper_crop

                self.yunet.setInputSize((net_w, net_h))
                _, faces = self.yunet.detect(input_img)

                if faces is not None and len(faces) > 0:
                    # Select face with highest confidence
                    best_face = max(faces, key=lambda f: float(f[-1]))
                    conf = float(best_face[-1])
                    
                    if conf >= self.score_threshold:
                        inv_scale = 1.0 / scale
                        fx = int(best_face[0] * inv_scale)
                        fy = int(best_face[1] * inv_scale)
                        fw = int(best_face[2] * inv_scale)
                        fh = int(best_face[3] * inv_scale)

                        # Add comfortable padding around face
                        pad_x = int(fw * 0.20)
                        pad_y = int(fh * 0.25)

                        abs_x1 = max(0, px1 + fx - pad_x)
                        abs_y1 = max(0, py1 + fy - pad_y)
                        abs_x2 = min(w, px1 + fx + fw + pad_x)
                        abs_y2 = min(h, py1 + fy + fh + pad_y)

                        face_crop = frame[abs_y1:abs_y2, abs_x1:abs_x2]
                        if face_crop.size > 0:
                            return {
                                "bbox": [abs_x1, abs_y1, abs_x2, abs_y2],
                                "face_crop": face_crop,
                                "has_real_face": True,
                                "confidence": round(conf, 3)
                            }
            except Exception as e:
                pass

        # 2. Fallback: If no real face is detected (e.g. facing away / back of head)
        # Extract upper 30% center region as head context, but clearly flag has_real_face = False
        head_top = py1
        head_bottom = min(h, py1 + int(p_height * 0.32))
        center_x = px1 + p_width // 2
        half_head_w = int(p_width * 0.30)
        head_left = max(0, center_x - half_head_w)
        head_right = min(w, center_x + half_head_w)

        head_crop = frame[head_top:head_bottom, head_left:head_right]
        if head_crop.size > 0 and (head_right - head_left) > 10 and (head_bottom - head_top) > 10:
            return {
                "bbox": [head_left, head_top, head_right, head_bottom],
                "face_crop": head_crop,
                "has_real_face": False,
                "confidence": 0.0
            }

        return None
