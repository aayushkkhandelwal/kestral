import os
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np
import config

class FaceDetector:
    """
    High-accuracy facial recognition & landmark detector utilizing OpenCV YuNet DNN and SFace.
    Accurately detects whether a real face (eyes, nose, mouth) is visible towards the camera,
    distinguishing true facial captures from back-of-head / turned-away views.
    Includes SFace facial feature embedding generation for face search and identity indexing.
    """
    def __init__(self, score_threshold: float = config.YUNET_SCORE_THRESHOLD):
        self.score_threshold = score_threshold
        self.yunet = None
        self.sface = None
        self.face_model_loaded = False
        self.face_recognizer_loaded = False
        
        # 1. Initialize YuNet Face Detector
        model_path = config.FACE_MODEL_PATH
        if os.path.exists(model_path) and hasattr(cv2, 'FaceDetectorYN_create'):
            try:
                self.yunet = cv2.FaceDetectorYN_create(
                    model_path,
                    "",
                    (320, 320),
                    score_threshold=self.score_threshold,
                    nms_threshold=config.YUNET_NMS_THRESHOLD
                )
                self.face_model_loaded = True
                print(f"[FaceDetector] Loaded YuNet face detector from {model_path}")
            except Exception as e:
                print(f"[FaceDetector] Error: YuNet initialization failed ({e})")
                self.face_model_loaded = False
        else:
            if not os.path.exists(model_path):
                print(f"[FaceDetector] ERROR: YuNet model not found at {model_path}. Run `python backend/scripts/download_models.py`")
            self.face_model_loaded = False

        # 2. Initialize SFace Feature Extractor for Face Search
        sface_path = config.SFACE_MODEL_PATH
        if os.path.exists(sface_path) and hasattr(cv2, 'FaceRecognizerSF_create'):
            try:
                self.sface = cv2.FaceRecognizerSF_create(sface_path, "")
                self.face_recognizer_loaded = True
                print(f"[FaceDetector] Loaded SFace recognizer from {sface_path}")
            except Exception as e:
                print(f"[FaceDetector] SFace recognizer initialization failed: {e}")
                self.face_recognizer_loaded = False

    def compute_embedding(self, frame: np.ndarray, face_data: np.ndarray) -> Optional[np.ndarray]:
        """
        Extracts a 128-dimensional L2-normalized feature embedding using SFace.
        """
        if self.sface is None or frame is None or face_data is None:
            return None
        try:
            # SFace expects the raw full frame and the raw 15-element face detection vector
            aligned_face = self.sface.alignCrop(frame, face_data)
            feature = self.sface.feature(aligned_face)
            norm = np.linalg.norm(feature)
            if norm > 0:
                feature = feature / norm
            return feature.flatten()
        except Exception as e:
            # Fallback: compute embedding directly on face crop
            try:
                if len(face_data.shape) == 1 and face_data.shape[0] >= 4:
                    fx, fy, fw, fh = [int(v) for v in face_data[:4]]
                    h, w = frame.shape[:2]
                    x1, y1 = max(0, fx), max(0, fy)
                    x2, y2 = min(w, fx + fw), min(h, fy + fh)
                    crop = frame[y1:y2, x1:x2]
                    if crop.size > 0:
                        resized = cv2.resize(crop, (112, 112))
                        feat = self.sface.feature(resized)
                        norm = np.linalg.norm(feat)
                        return (feat / norm).flatten() if norm > 0 else feat.flatten()
            except Exception:
                pass
            return None

    def detect_face_in_person(
        self, frame: np.ndarray, person_bbox: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Locates the face within a person's upper body.
        Applies upper-body upscaling for distant or low-resolution CCTV subjects.
        Returns:
            - 'bbox': [fx1, fy1, fx2, fy2]
            - 'face_crop': cropped image
            - 'has_real_face': True if facial features were verified by neural network
            - 'confidence': confidence score (0.0 to 1.0)
            - 'landmarks': 5 facial landmarks in original frame coordinates
            - 'embedding': 128-d feature vector or None
        """
        if frame is None or frame.size == 0:
            return None

        h, w = frame.shape[:2]
        px1, py1, px2, py2 = person_bbox
        px1, py1 = max(0, px1), max(0, py1)
        px2, py2 = min(w, px2), min(h, py2)

        p_width = px2 - px1
        p_height = py2 - py1

        if p_width < 12 or p_height < 20:
            return None

        # Focus face search on upper 55% of person (head, face, neck)
        head_region_h = int(p_height * 0.55)
        crop_y2 = min(h, py1 + head_region_h)
        upper_crop = frame[py1:crop_y2, px1:px2]

        if upper_crop.size == 0:
            return None

        uh, uw = upper_crop.shape[:2]

        # 1. Try Deep Face Detector (YuNet)
        if self.yunet is not None and self.face_model_loaded and uw >= 15 and uh >= 15:
            try:
                # Upscale small crops to ensure YuNet detects distant/small ATM faces (T1.2)
                upscale = 1.0
                if max(uw, uh) < 140:
                    upscale = 2.0
                    input_img = cv2.resize(upper_crop, (int(uw * upscale), int(uh * upscale)), interpolation=cv2.INTER_LINEAR)
                    net_w, net_h = int(uw * upscale), int(uh * upscale)
                elif max(uw, uh) > 480:
                    downscale = 360.0 / max(uw, uh)
                    input_img = cv2.resize(upper_crop, (int(uw * downscale), int(uh * downscale)), interpolation=cv2.INTER_AREA)
                    upscale = downscale
                    net_w, net_h = int(uw * downscale), int(uh * downscale)
                else:
                    input_img = upper_crop
                    net_w, net_h = uw, uh

                self.yunet.setInputSize((net_w, net_h))
                _, faces = self.yunet.detect(input_img)

                if faces is not None and len(faces) > 0:
                    best_face = max(faces, key=lambda f: float(f[-1]))
                    conf = float(best_face[-1])
                    
                    if conf >= self.score_threshold:
                        inv_scale = 1.0 / upscale
                        fx = int(best_face[0] * inv_scale)
                        fy = int(best_face[1] * inv_scale)
                        fw = int(best_face[2] * inv_scale)
                        fh = int(best_face[3] * inv_scale)

                        # Comfortable padding around face
                        pad_x = int(fw * 0.18)
                        pad_y = int(fh * 0.22)

                        abs_x1 = max(0, px1 + fx - pad_x)
                        abs_y1 = max(0, py1 + fy - pad_y)
                        abs_x2 = min(w, px1 + fx + fw + pad_x)
                        abs_y2 = min(h, py1 + fy + fh + pad_y)

                        face_crop = frame[abs_y1:abs_y2, abs_x1:abs_x2]
                        if face_crop.size > 0:
                            # Map landmarks back to original frame
                            raw_landmarks = best_face[4:14].reshape(5, 2)
                            abs_landmarks = []
                            for pt in raw_landmarks:
                                lx = int(max(0, min(w - 1, px1 + (pt[0] * inv_scale))))
                                ly = int(max(0, min(h - 1, py1 + (pt[1] * inv_scale))))
                                abs_landmarks.append([lx, ly])

                            # Create full-frame face detection record for SFace
                            full_face_vec = best_face.copy()
                            full_face_vec[0] = px1 + fx
                            full_face_vec[1] = py1 + fy
                            full_face_vec[2] = fw
                            full_face_vec[3] = fh
                            for idx, pt in enumerate(abs_landmarks):
                                full_face_vec[4 + idx * 2] = pt[0]
                                full_face_vec[5 + idx * 2] = pt[1]

                            embedding = self.compute_embedding(frame, full_face_vec)

                            return {
                                "bbox": [abs_x1, abs_y1, abs_x2, abs_y2],
                                "face_crop": face_crop,
                                "has_real_face": True,
                                "confidence": round(conf, 3),
                                "landmarks": abs_landmarks,
                                "embedding": embedding.tolist() if embedding is not None else None
                            }
            except Exception as e:
                print(f"[FaceDetector] Error detecting face in person: {e}")

        # 2. Fallback: Upper head region context when facing away / back of head
        # Clearly flagged with has_real_face = False
        head_top = py1
        head_bottom = min(h, py1 + int(p_height * 0.32))
        center_x = px1 + p_width // 2
        half_head_w = int(p_width * 0.28)
        head_left = max(0, center_x - half_head_w)
        head_right = min(w, center_x + half_head_w)

        head_crop = frame[head_top:head_bottom, head_left:head_right]
        if head_crop.size > 0 and (head_right - head_left) > 10 and (head_bottom - head_top) > 10:
            return {
                "bbox": [head_left, head_top, head_right, head_bottom],
                "face_crop": head_crop,
                "has_real_face": False,
                "confidence": 0.0,
                "landmarks": [],
                "embedding": None
            }

        return None
