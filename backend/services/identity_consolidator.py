"""
Kestral AI — Biometric & Appearance Identity Consolidator (Re-ID).
Unifies fragmented tracks of the same individual across long surveillance clips
by evaluating temporal non-overlap, facial biometric similarity, and upper-body clothing signatures.
"""

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
        face_sim_threshold: float = 0.72,
        clothing_sim_threshold: float = 0.78,
        min_temporal_gap_sec: float = 0.5
    ):
        self.face_sim_threshold = face_sim_threshold
        self.clothing_sim_threshold = clothing_sim_threshold
        self.min_temporal_gap_sec = min_temporal_gap_sec

    @staticmethod
    def _extract_clothing_hist(full_frame: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """Extracts normalized 2D HSV color histogram of the upper torso / clothing."""
        if full_frame is None or full_frame.size == 0 or not bbox:
            return None
        x1, y1, x2, y2 = bbox
        h, w = y2 - y1, x2 - x1
        if h < 20 or w < 20:
            return None

        # Torso: 20% down from top to 65% down, inner 80% width to avoid background
        torso_y1 = int(max(0, y1 + h * 0.20))
        torso_y2 = int(min(full_frame.shape[0], y1 + h * 0.65))
        torso_x1 = int(max(0, x1 + w * 0.10))
        torso_x2 = int(min(full_frame.shape[1], x1 + w * 0.90))

        if torso_y2 <= torso_y1 or torso_x2 <= torso_x1:
            return None

        torso_crop = full_frame[torso_y1:torso_y2, torso_x1:torso_x2]
        if torso_crop.size == 0:
            return None

        hsv = cv2.cvtColor(torso_crop, cv2.COLOR_BGR2HSV)
        # 16 Hue bins x 16 Saturation bins
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        return hist

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
        # 8-bin gradient orientation histogram
        grad_hist, _ = np.histogram(angle, bins=8, range=(0, 360), weights=mag)
        grad_norm = float(np.linalg.norm(grad_hist))
        if grad_norm > 0:
            grad_hist = grad_hist / grad_norm
        else:
            grad_hist = np.ones(8, dtype=np.float32) / np.sqrt(8.0)

        return hist, grad_hist

    def _compare_appearance(
        self,
        t1: Dict[str, Any],
        t2: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Determines whether two non-overlapping tracks belong to the same person.
        Returns (is_match, confidence_score, reason).
        """
        # 1. Check temporal non-overlap (One person cannot be in two places simultaneously)
        start1, end1 = t1["first_seen_time"], t1["last_seen_time"]
        start2, end2 = t2["first_seen_time"], t2["last_seen_time"]

        # If they overlap by more than min_temporal_gap_sec, they are distinct people!
        overlap = min(end1, end2) - max(start1, start2)
        if overlap > self.min_temporal_gap_sec:
            return False, 0.0, "TEMPORAL_OVERLAP"

        # 2. Extract clothing histograms
        h_cloth1 = self._extract_clothing_hist(t1.get("best_full_frame"), t1.get("best_person_bbox"))
        h_cloth2 = self._extract_clothing_hist(t2.get("best_full_frame"), t2.get("best_person_bbox"))

        clothing_sim = 0.0
        if h_cloth1 is not None and h_cloth2 is not None:
            # Bhattacharyya distance (0 = identical, 1 = completely different)
            bhatt = cv2.compareHist(h_cloth1, h_cloth2, cv2.HISTCMP_BHATTACHARYYA)
            clothing_sim = max(0.0, 1.0 - float(bhatt))

        # 3. Extract face signatures if both have real face detections
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

        # 4. Decision Rule
        if both_faces:
            # When both have faces, require high face agreement and supporting clothing match
            combined = 0.60 * face_sim + 0.40 * clothing_sim
            if face_sim >= self.face_sim_threshold and clothing_sim >= 0.60:
                return True, round(combined, 3), "BIOMETRIC_AND_CLOTHING_MATCH"
            if combined >= 0.75:
                return True, round(combined, 3), "COMPOSITE_MATCH"
        else:
            # When one or both face crops are obscured (e.g. looking down/back of head),
            # require very high clothing match (>0.82)
            if clothing_sim >= self.clothing_sim_threshold:
                return True, round(clothing_sim, 3), "CLOTHING_REID_MATCH"

        return False, round(max(face_sim, clothing_sim), 3), "NO_MATCH"

    def consolidate_tracks(self, tracks: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Groups track fragments belonging to the same individual into consolidated unique identities.
        Returns consolidated tracks dictionary.
        """
        if not tracks or len(tracks) <= 1:
            return tracks

        track_ids = sorted(tracks.keys())
        # Disjoint set / Union-Find for track clustering
        parent = {tid: tid for tid in track_ids}

        def find(i):
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                # Merge into the smaller ID for consistent numbering
                if root_i < root_j:
                    parent[root_j] = root_i
                else:
                    parent[root_i] = root_j

        # Pairwise comparison across all tracks
        for i in range(len(track_ids)):
            id_i = track_ids[i]
            for j in range(i + 1, len(track_ids)):
                id_j = track_ids[j]
                matched, score, reason = self._compare_appearance(tracks[id_i], tracks[id_j])
                if matched:
                    # Double-check: ensure id_j does not temporally overlap with ANY existing member of id_i's cluster
                    root_i = find(id_i)
                    cluster_members = [tid for tid in track_ids if find(tid) == root_i]
                    can_merge = True
                    for m_id in cluster_members:
                        ov = min(tracks[m_id]["last_seen_time"], tracks[id_j]["last_seen_time"]) - max(
                            tracks[m_id]["first_seen_time"], tracks[id_j]["first_seen_time"]
                        )
                        if ov > self.min_temporal_gap_sec:
                            can_merge = False
                            break

                    if can_merge:
                        union(id_i, id_j)

        # Assemble consolidated clusters
        clusters: Dict[int, List[int]] = {}
        for tid in track_ids:
            root = find(tid)
            clusters.setdefault(root, []).append(tid)

        consolidated: Dict[int, Dict[str, Any]] = {}
        for root_id, member_ids in clusters.items():
            if len(member_ids) == 1:
                # Unmodified single track
                consolidated[root_id] = tracks[root_id]
                consolidated[root_id]["consolidated_track_ids"] = [root_id]
                continue

            # Multi-fragment cluster: merge metadata and pick BEST evidence frame
            member_tracks = [tracks[m] for m in member_ids]

            # Select candidate with highest quality score and real face
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
                "best_quality": best_member["best_quality"],
                "best_full_frame": best_member["best_full_frame"],
                "best_face_crop": best_member["best_face_crop"],
                "all_scores": all_scores_merged,
                "consolidated_track_ids": sorted(member_ids)
            }
            consolidated[root_id] = merged_track

        return consolidated
