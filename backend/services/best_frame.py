import os
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

class BestFrameSelector:
    """
    Manages identity tracks across video sequences and isolates the single highest quality
    evidence frame and face crop per tracked individual.
    Prioritizes verified facial captures with eyes/nose/mouth over back-of-head or occluded frames.
    """
    def __init__(self, output_dir: str, consolidate_identities: bool = True):
        self.output_dir = output_dir
        self.consolidate_identities = consolidate_identities
        os.makedirs(output_dir, exist_ok=True)
        self.tracks: Dict[int, Dict[str, Any]] = {}

    def update_track(
        self,
        track_id: int,
        frame_idx: int,
        timestamp_sec: float,
        full_frame: np.ndarray,
        person_bbox: List[int],
        face_info: Optional[Dict[str, Any]],
        quality_metrics: Dict[str, Any]
    ):
        score = quality_metrics.get("overall_score", 0.0)
        has_real_face = quality_metrics.get("has_real_face", False)

        if track_id not in self.tracks:
            self.tracks[track_id] = {
                "track_id": track_id,
                "first_seen_frame": frame_idx,
                "last_seen_frame": frame_idx,
                "first_seen_time": timestamp_sec,
                "last_seen_time": timestamp_sec,
                "total_detections": 1,
                "best_score": score,
                "best_has_real_face": has_real_face,
                "best_frame_idx": frame_idx,
                "best_timestamp": timestamp_sec,
                "best_person_bbox": person_bbox,
                "best_face_bbox": face_info.get("bbox") if face_info else None,
                "best_quality": quality_metrics,
                "best_full_frame": full_frame.copy(),
                "best_face_crop": face_info.get("face_crop").copy() if face_info and face_info.get("face_crop") is not None else None,
                "all_scores": [score]
            }
        else:
            t = self.tracks[track_id]
            t["last_seen_frame"] = frame_idx
            t["last_seen_time"] = timestamp_sec
            t["total_detections"] += 1
            t["all_scores"].append(score)

            prev_real = t.get("best_has_real_face", False)
            should_replace = False

            if has_real_face and not prev_real:
                # Immediate upgrade: Found a real face compared to previously only seeing back of head!
                should_replace = True
            elif has_real_face == prev_real:
                if score > t["best_score"] or t["best_face_crop"] is None:
                    should_replace = True

            if should_replace:
                t["best_score"] = score
                t["best_has_real_face"] = has_real_face
                t["best_frame_idx"] = frame_idx
                t["best_timestamp"] = timestamp_sec
                t["best_person_bbox"] = person_bbox
                t["best_face_bbox"] = face_info.get("bbox") if face_info else None
                t["best_quality"] = quality_metrics
                t["best_full_frame"] = full_frame.copy()
                if face_info and face_info.get("face_crop") is not None:
                    t["best_face_crop"] = face_info.get("face_crop").copy()

    def finalize(self, relative_url_prefix: str = "") -> List[Dict[str, Any]]:
        # Consolidate non-overlapping fragmented tracks of the same individual
        if self.consolidate_identities and len(self.tracks) > 1:
            try:
                from services.identity_consolidator import IdentityConsolidator
                consolidator = IdentityConsolidator()
                self.tracks = consolidator.consolidate_tracks(self.tracks)
            except Exception as e:
                print(f"[BestFrameSelector] Identity consolidation warning: {e}")

        finalized_tracks: List[Dict[str, Any]] = []

        for track_id, data in self.tracks.items():
            face_crop_filename = f"track_{track_id}_face.jpg"
            full_frame_filename = f"track_{track_id}_full.jpg"
            
            face_crop_path = os.path.join(self.output_dir, face_crop_filename)
            full_frame_path = os.path.join(self.output_dir, full_frame_filename)

            # Draw visual evidence bounding boxes on the full frame
            annotated_frame = data["best_full_frame"].copy()
            px1, py1, px2, py2 = data["best_person_bbox"]
            cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), (16, 185, 129), 2) # Emerald person bbox
            
            has_face = data.get("best_has_real_face", False)
            label = f"ID #{track_id} | Face: {'YES' if has_face else 'OCCLUDED'}"
            cv2.putText(
                annotated_frame,
                label,
                (px1, max(25, py1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (16, 185, 129),
                2,
                cv2.LINE_AA
            )

            if data["best_face_bbox"] and has_face:
                fx1, fy1, fx2, fy2 = data["best_face_bbox"]
                cv2.rectangle(annotated_frame, (fx1, fy1), (fx2, fy2), (6, 182, 212), 2) # Cyan face bbox

            cv2.imwrite(full_frame_path, annotated_frame)

            # Save best face/head crop
            if data["best_face_crop"] is not None and data["best_face_crop"].size > 0:
                cv2.imwrite(face_crop_path, data["best_face_crop"])
            else:
                person_crop = data["best_full_frame"][py1:py2, px1:px2]
                cv2.imwrite(face_crop_path, person_crop)

            # Compute cryptographic hashes for forensic integrity
            face_sha256 = self._compute_sha256(face_crop_path)
            full_frame_sha256 = self._compute_sha256(full_frame_path)

            duration = round(data["last_seen_time"] - data["first_seen_time"], 2)
            avg_score = round(float(np.mean(data["all_scores"])), 1) if data["all_scores"] else 0.0

            clean_summary = {
                "track_id": track_id,
                "first_seen_time": round(data["first_seen_time"], 2),
                "last_seen_time": round(data["last_seen_time"], 2),
                "duration_seconds": duration,
                "total_detections": data["total_detections"],
                "best_frame_idx": data["best_frame_idx"],
                "best_timestamp": round(data["best_timestamp"], 2),
                "best_score": data["best_score"],
                "has_real_face": has_face,
                "average_score": avg_score,
                "quality": data["best_quality"],
                "person_bbox": data["best_person_bbox"],
                "face_bbox": data["best_face_bbox"],
                "face_image_url": f"{relative_url_prefix}/{face_crop_filename}".replace("//", "/"),
                "crop_url": f"{relative_url_prefix}/{face_crop_filename}".replace("//", "/"),
                "full_frame_url": f"{relative_url_prefix}/{full_frame_filename}".replace("//", "/"),
                "face_sha256": face_sha256,
                "full_frame_sha256": full_frame_sha256,
                "consolidated_track_ids": data.get("consolidated_track_ids", [track_id])
            }
            finalized_tracks.append(clean_summary)

        # Sort: verified faces first, then by score
        finalized_tracks.sort(key=lambda x: (x["has_real_face"], x["best_score"]), reverse=True)
        return finalized_tracks

    @staticmethod
    def _compute_sha256(filepath: str) -> str:
        import hashlib
        if not os.path.exists(filepath):
            return ""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
