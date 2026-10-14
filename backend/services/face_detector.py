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

    def detect_faces(
        self, frame: np.ndarray, score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects all faces in the provided frame using deep learning face detection.
        Extracts face bounding boxes, confidence scores, and 5 facial landmarks
        (right eye, left eye, nose tip, right mouth corner, left mouth corner).
        """
        if frame is None or frame.size == 0 or self.yunet is None:
            return []

        h, w = frame.shape[:2]
        thresh = score_threshold if score_threshold is not None else self.score_threshold

        try:
            self.yunet.setInputSize((w, h))
            if hasattr(self.yunet, "setScoreThreshold"):
                self.yunet.setScoreThreshold(thresh)
            _, faces = self.yunet.detect(frame)

            if faces is None or len(faces) == 0:
                return []

            results = []
            for face in faces:
                conf = float(face[-1])
                if conf < thresh:
                    continue

                fx = int(face[0])
                fy = int(face[1])
                fw = int(face[2])
                fh = int(face[3])

                x1 = int(max(0, min(w - 1, fx)))
                y1 = int(max(0, min(h - 1, fy)))
                x2 = int(max(0, min(w, fx + fw)))
                y2 = int(max(0, min(h, fy + fh)))

                if x2 <= x1 or y2 <= y1:
                    continue

                # 5 facial landmarks: right eye, left eye, nose tip, right mouth, left mouth
                landmarks_raw = face[4:14].reshape(5, 2)
                landmarks = []
                for pt in landmarks_raw:
                    lx = int(max(0, min(w - 1, pt[0])))
                    ly = int(max(0, min(h - 1, pt[1])))
                    landmarks.append([lx, ly])

                landmarks_named = {
                    "right_eye": landmarks[0],
                    "left_eye": landmarks[1],
                    "nose": landmarks[2],
                    "right_mouth": landmarks[3],
                    "left_mouth": landmarks[4]
                }

                results.append({
                    "bbox": [x1, y1, x2, y2],
                    "width": x2 - x1,
                    "height": y2 - y1,
                    "confidence": round(conf, 3),
                    "landmarks": landmarks,
                    "landmarks_named": landmarks_named
                })

            return results
        except Exception as e:
            print(f"[FaceDetector] detect_faces error: {e}")
            return []

    @staticmethod
    def associate_faces_with_people(
        people: List[Dict[str, Any]], faces: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Spatially associates detected faces with tracked persons.
        Matches a face to a person if the face center or substantial area falls
        within the person bounding box.
        """
        for face in faces:
            face["matched_track_id"] = None

        for person in people:
            px1, py1, px2, py2 = person["bbox"]
            best_face = None
            best_overlap = 0.0

            for face in faces:
                if face.get("matched_track_id") is not None:
                    continue

                fx1, fy1, fx2, fy2 = face["bbox"]
                fcx = (fx1 + fx2) / 2.0
                fcy = (fy1 + fy2) / 2.0

                # Face center inside person bounding box
                if px1 <= fcx <= px2 and py1 <= fcy <= py2:
                    ix1 = max(px1, fx1)
                    iy1 = max(py1, fy1)
                    ix2 = min(px2, fx2)
                    iy2 = min(py2, fy2)
                    inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                    f_area = max(1, (fx2 - fx1) * (fy2 - fy1))
                    overlap = inter_area / f_area

                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_face = face

            if best_face is not None and best_overlap >= 0.30:
                best_face["matched_track_id"] = person["track_id"]
                person["face_bbox"] = best_face["bbox"]
                person["face_confidence"] = best_face["confidence"]
                person["landmarks"] = best_face.get("landmarks", [])
            else:
                person["face_bbox"] = None
                person["face_confidence"] = None
                person["landmarks"] = []

        return people, faces
