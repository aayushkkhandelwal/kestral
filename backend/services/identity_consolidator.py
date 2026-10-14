"""
Kestral AI — Biometric & Appearance Identity Consolidator (Re-ID).
Unifies fragmented tracks of the same individual across long surveillance clips
by evaluating temporal non-overlap, facial biometric similarity (SFace/YuNet),
and upper-body clothing signatures across multiple angles and postures.
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional


class IdentityConsolidator:
    """
    Consolidates fragmented tracks caused by occlusion, head turns, or re-entries.
    Preserves forensic integrity while reducing redundant evidence cards for the same human.
    """

    def __init__(
        self,
        face_sim_threshold: float = 0.363,
        clothing_sim_threshold: float = 0.58,
        min_temporal_gap_sec: float = 0.5,
        max_handover_overlap_sec: float = 2.5
    ):
        self.face_sim_threshold = face_sim_threshold
        self.clothing_sim_threshold = clothing_sim_threshold
        self.min_temporal_gap_sec = min_temporal_gap_sec
        self.max_handover_overlap_sec = max_handover_overlap_sec

        # Initialize SFace Deep Biometric Recognizer if available
        self.recognizer = None
        self.yunet_model = None
        
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sface_path = os.path.join(backend_dir, "models", "face_recognition_sface.onnx")
        yunet_path = os.path.join(backend_dir, "models", "face_detection_yunet.onnx")

        if os.path.exists(sface_path) and hasattr(cv2, 'FaceRecognizerSF_create'):
            try:
                self.recognizer = cv2.FaceRecognizerSF_create(sface_path, "")
            except Exception as e:
                print(f"[IdentityConsolidator] SFace initialization note: {e}")

        self.yunet_path = yunet_path if os.path.exists(yunet_path) else None

    def _extract_sface_embedding(self, face_crop: Optional[np.ndarray]) -> Optional[np.ndarray]:
        """Extracts 128-dimensional deep biometric embedding using OpenCV SFace."""
        if self.recognizer is None or face_crop is None or face_crop.size == 0:
            return None
        h, w = face_crop.shape[:2]
        if h < 20 or w < 20:
            return None
        try:
            if self.yunet_path:
                yunet = cv2.FaceDetectorYN_create(self.yunet_path, "", (w, h), score_threshold=0.3)
                _, faces = yunet.detect(face_crop)
                if faces is not None and len(faces) > 0:
                    aligned = self.recognizer.alignCrop(face_crop, faces[0])
                    return self.recognizer.feature(aligned)
            resized = cv2.resize(face_crop, (112, 112))
            return self.recognizer.feature(resized)
        except Exception:
            return None

    @staticmethod
    def _extract_smart_torso(
        full_frame: Optional[np.ndarray],
        p_bbox: Optional[List[int]],
        f_bbox: Optional[List[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """Extracts upper-body torso signature relative to face if present, or person bbox."""
        if full_frame is None or full_frame.size == 0 or not p_bbox:
            return None
        h_img, w_img = full_frame.shape[:2]
        crop = None

        # 1. Prefer region directly below face (neck & chest)
        if f_bbox:
            fx1, fy1, fx2, fy2 = f_bbox
            fw = max(1, fx2 - fx1)
            fh = max(1, fy2 - fy1)
            cx = (fx1 + fx2) // 2
            tx1 = max(0, int(cx - fw * 0.85))
            tx2 = min(w_img, int(cx + fw * 0.85))
            ty1 = max(0, int(fy2 + fh * 0.10))
            ty2 = min(h_img, int(fy2 + fh * 1.50))
            if ty2 > ty1 and tx2 > tx1:
                candidate = full_frame[ty1:ty2, tx1:tx2]
                if candidate.size >= 100:
                    crop = candidate

        # 2. Fallback to upper 25%-65% of person bbox
        if crop is None:
            px1, py1, px2, py2 = p_bbox
            pw = max(1, px2 - px1)
            ph = max(1, py2 - py1)
            ty1 = int(py1 + ph * 0.20)
            ty2 = int(py1 + ph * 0.65)
            tx1 = int(px1 + pw * 0.15)
            tx2 = int(px1 + pw * 0.85)
            candidate = full_frame[max(0, ty1):min(h_img, ty2), max(0, tx1):min(w_img, tx2)]
            if candidate.size >= 100:
                crop = candidate

        if crop is None or crop.size == 0:
            return None

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [12, 12], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        mean_bgr = cv2.mean(crop)[:3]
        return {"hist": hist, "mean_bgr": mean_bgr}

    @staticmethod
    def _extract_clothing_hist(full_frame: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """Backward-compatible 2D HSV color histogram extraction."""
        torso = IdentityConsolidator._extract_smart_torso(full_frame, bbox)
        return torso["hist"] if torso else None

    @staticmethod
    def _extract_face_signature(face_crop: np.ndarray) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Extracts normalized facial color histogram and gradient structure."""
        if face_crop is None or face_crop.size == 0:
            return None

        resized = cv2.resize(face_crop, (96, 96))
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # 1. Color distribution (skin tone + hair)
        hist = cv2.calcHist([hsv], [0, 1], None, [12, 12], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

        # 2. Structural gradient (Sobel edge orientation)
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)
        grad_hist, _ = np.histogram(angle, bins=8, range=(0, 360), weights=mag)
        grad_norm = float(np.linalg.norm(grad_hist))
        if grad_norm > 0:
            grad_hist = grad_hist / grad_norm
        else:
            grad_hist = np.ones(8, dtype=np.float32) / np.sqrt(8.0)

        return hist, grad_hist

    def _compare_clothing_signatures(
        self,
        sig1: Optional[Dict[str, Any]],
        sig2: Optional[Dict[str, Any]]
    ) -> float:
        """Computes hybrid similarity between two upper-body clothing signatures."""
        if sig1 is None or sig2 is None:
            return 0.0
        # 1. Histogram similarity (Bhattacharyya)
        bhatt = cv2.compareHist(sig1["hist"], sig2["hist"], cv2.HISTCMP_BHATTACHARYYA)
        hist_sim = max(0.0, 1.0 - float(bhatt))
        # 2. Mean color proximity (Euclidean)
        m1 = np.array(sig1["mean_bgr"])
        m2 = np.array(sig2["mean_bgr"])
        dist = np.linalg.norm(m1 - m2)
        color_sim = max(0.0, 1.0 - (dist / 180.0))
        return 0.5 * hist_sim + 0.5 * color_sim

    def _compare_appearance(
        self,
        t1: Dict[str, Any],
        t2: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Determines whether two tracks belong to the same person.
        Supports both deep SFace biometric embeddings and spatial clothing Re-ID.
        """
        start1, end1 = t1["first_seen_time"], t1["last_seen_time"]
        start2, end2 = t2["first_seen_time"], t2["last_seen_time"]
        overlap = min(end1, end2) - max(start1, start2)

        # Extract clothing signatures
        cloth1 = self._extract_smart_torso(
            t1.get("best_full_frame"),
            t1.get("best_person_bbox"),
            t1.get("best_face_bbox")
        )
        cloth2 = self._extract_smart_torso(
            t2.get("best_full_frame"),
            t2.get("best_person_bbox"),
            t2.get("best_face_bbox")
        )
        clothing_sim = self._compare_clothing_signatures(cloth1, cloth2)

        # 1. Immediate Track Handover (Kalman tracker drop & recovery at same spot)
        if 0.0 <= overlap <= self.max_handover_overlap_sec and clothing_sim >= 0.55:
            return True, round(clothing_sim, 3), "TRACK_HANDOVER"

        # If they overlap by more than min_temporal_gap_sec, they are distinct people!
        if overlap > self.min_temporal_gap_sec:
            return False, 0.0, "TEMPORAL_OVERLAP"

        # 2. Deep SFace Biometric Verification
        sface1 = self._extract_sface_embedding(t1.get("best_face_crop")) if t1.get("best_has_real_face") else None
        sface2 = self._extract_sface_embedding(t2.get("best_face_crop")) if t2.get("best_has_real_face") else None

        if sface1 is not None and sface2 is not None and self.recognizer is not None:
            sface_sim = float(self.recognizer.match(sface1, sface2, cv2.FaceRecognizerSF_FR_COSINE))
            if sface_sim >= self.face_sim_threshold:
                return True, round(sface_sim, 3), "BIOMETRIC_SFACE_MATCH"

        # 3. Traditional Facial Color + Structural Feature (fallback)
        f1 = t1.get("best_face_crop")
        f2 = t2.get("best_face_crop")
        has_face1 = t1.get("best_has_real_face", False)
        has_face2 = t2.get("best_has_real_face", False)
        face_sim = 0.0
        both_faces = False

        if has_face1 and has_face2 and f1 is not None and f2 is not None:
            sig1 = self._extract_face_signature(f1)
            sig2 = self._extract_face_signature(f2)
            if sig1 is not None and sig2 is not None:
                h_face1, g_face1 = sig1
                h_face2, g_face2 = sig2
                f_bhatt = cv2.compareHist(h_face1, h_face2, cv2.HISTCMP_BHATTACHARYYA)
                f_color_sim = max(0.0, 1.0 - float(f_bhatt))
                f_struct_sim = float(np.dot(g_face1, g_face2))
                face_sim = 0.5 * f_color_sim + 0.5 * max(0.0, f_struct_sim)
                both_faces = True

        if both_faces:
            combined = 0.60 * face_sim + 0.40 * clothing_sim
            if face_sim >= 0.70 and clothing_sim >= 0.50:
                return True, round(combined, 3), "BIOMETRIC_AND_CLOTHING_MATCH"
            if combined >= 0.68:
                return True, round(combined, 3), "COMPOSITE_MATCH"
        else:
            if clothing_sim >= self.clothing_sim_threshold:
                return True, round(clothing_sim, 3), "CLOTHING_REID_MATCH"

        # 4. Contextual Re-ID (same scene / camera location across episodes)
        p1 = t1.get("best_person_bbox")
        p2 = t2.get("best_person_bbox")
        if p1 and p2 and clothing_sim >= 0.45:
            # Check if both appear in the main focal area (e.g. ATM console)
            if abs(p1[0] - p2[0]) < 180 and abs(p1[2] - p2[2]) < 180:
                return True, round(clothing_sim, 3), "SPATIAL_APPEARANCE_REID"

        return False, round(max(face_sim, clothing_sim), 3), "NO_MATCH"

    def consolidate_tracks(self, tracks: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Groups track fragments belonging to the same individual into consolidated unique identities.
        Filters out single-second transient artifacts and resolves angle variations.
        """
        if not tracks or len(tracks) <= 1:
            return tracks

        # 1. Filter transient edge/ghost fragments (< 2.0s duration, < 6 detections without verified face)
        valid_track_ids = []
        for tid, t in sorted(tracks.items()):
            dur = t.get("last_seen_time", 0.0) - t.get("first_seen_time", 0.0)
            dets = t.get("total_detections", 1)
            has_face = t.get("best_has_real_face", False)
            if dur < 2.0 and dets < 6 and not has_face and len(tracks) > 2:
                # Ghost edge fragment ignored from primary evidence cards
                continue
            valid_track_ids.append(tid)

        if not valid_track_ids:
            valid_track_ids = sorted(tracks.keys())

        # Disjoint set / Union-Find for track clustering
        parent = {tid: tid for tid in valid_track_ids}

        def find(i):
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                if root_i < root_j:
                    parent[root_j] = root_i
                else:
                    parent[root_i] = root_j

        def clusters_temporally_overlap(root_a: int, root_b: int) -> bool:
            """Ensures no member of cluster A overlaps (> max_handover) with any member of cluster B."""
            members_a = [tid for tid in valid_track_ids if find(tid) == root_a]
            members_b = [tid for tid in valid_track_ids if find(tid) == root_b]
            for ma in members_a:
                for mb in members_b:
                    ta = tracks[ma]
                    tb = tracks[mb]
                    ov = min(ta["last_seen_time"], tb["last_seen_time"]) - max(
                        ta["first_seen_time"], tb["first_seen_time"]
                    )
                    if ov > self.max_handover_overlap_sec:
                        return True
            return False

        # Evaluate candidate merges across all pairs
        candidates = []
        for i in range(len(valid_track_ids)):
            id_i = valid_track_ids[i]
            for j in range(i + 1, len(valid_track_ids)):
                id_j = valid_track_ids[j]
                matched, score, reason = self._compare_appearance(tracks[id_i], tracks[id_j])
                if matched:
                    candidates.append((score, id_i, id_j, reason))

        # Merge highest confidence matches first
        candidates.sort(key=lambda c: c[0], reverse=True)
        for score, id_i, id_j, reason in candidates:
            root_i = find(id_i)
            root_j = find(id_j)
            if root_i != root_j:
                if not clusters_temporally_overlap(root_i, root_j):
                    union(id_i, id_j)

        # Assemble consolidated clusters
        clusters: Dict[int, List[int]] = {}
        for tid in valid_track_ids:
            root = find(tid)
            clusters.setdefault(root, []).append(tid)

        consolidated: Dict[int, Dict[str, Any]] = {}
        for root_id, member_ids in clusters.items():
            if len(member_ids) == 1:
                consolidated[root_id] = tracks[root_id]
                consolidated[root_id]["consolidated_track_ids"] = [root_id]
                continue

            member_tracks = [tracks[m] for m in member_ids]

            # Select candidate with highest quality score and verified real face
            best_member = max(
                member_tracks,
                key=lambda t: (1 if t.get("best_has_real_face") else 0, t.get("best_score", 0.0))
            )

            min_time = min(t["first_seen_time"] for t in member_tracks)
            max_time = max(t["last_seen_time"] for t in member_tracks)
            min_frame = min(t["first_seen_frame"] for t in member_tracks)
            max_frame = max(t["last_seen_frame"] for t in member_tracks)
            total_dets = sum(t["total_detections"] for t in member_tracks)
            all_scores_merged = [s for t in member_tracks for s in t.get("all_scores", [])]

            merged_track = {
                "track_id": root_id,
                "first_seen_frame": min_frame,
                "last_seen_frame": max_frame,
                "first_seen_time": min_time,
                "last_seen_time": max_time,
                "total_detections": total_dets,
                "best_score": best_member["best_score"],
                "best_has_real_face": best_member["best_has_real_face"],
                "best_frame_idx": best_member["best_frame_idx"],
                "best_timestamp": best_member["best_timestamp"],
                "best_person_bbox": best_member["best_person_bbox"],
                "best_face_bbox": best_member["best_face_bbox"],
                "best_quality": best_member.get("best_quality") or best_member.get("quality", {}),
                "best_full_frame": best_member.get("best_full_frame"),
                "best_face_crop": best_member.get("best_face_crop"),
                "all_scores": all_scores_merged,
                "consolidated_track_ids": sorted(member_ids)
            }
            consolidated[root_id] = merged_track

        return consolidated
