import os
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

class BestFrameSelector:
    """
    Manages identity tracks across video sequences and isolates the single highest quality
    evidence frame and face crop per tracked individual.
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # track_id -> track data dictionary
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
        """
        Registers an observation for a tracked subject and retains the candidate with superior quality metrics.
        """
        score = quality_metrics.get("overall_score", 0.0)

        if track_id not in self.tracks:
            self.tracks[track_id] = {
                "track_id": track_id,
                "first_seen_frame": frame_idx,
                "last_seen_frame": frame_idx,
                "first_seen_time": timestamp_sec,
                "last_seen_time": timestamp_sec,
                "total_detections": 1,
                "best_score": score,
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

            # Update best frame if current frame scores higher
            if score > t["best_score"] or t["best_face_crop"] is None:
                t["best_score"] = score
                t["best_frame_idx"] = frame_idx
                t["best_timestamp"] = timestamp_sec
                t["best_person_bbox"] = person_bbox
                t["best_face_bbox"] = face_info.get("bbox") if face_info else None
                t["best_quality"] = quality_metrics
                t["best_full_frame"] = full_frame.copy()
                if face_info and face_info.get("face_crop") is not None:
                    t["best_face_crop"] = face_info.get("face_crop").copy()

    def finalize(self, relative_url_prefix: str = "") -> List[Dict[str, Any]]:
        """
        Saves all top-rated evidence crops to disk and compiles finalized track summary statistics.
        
        Args:
            relative_url_prefix: URL path prefix for frontend asset retrieval (e.g. '/results/task_123/')
            
        Returns:
            List of track summaries with saved image paths and performance analytics.
        """
        finalized_tracks: List[Dict[str, Any]] = []

        for track_id, data in self.tracks.items():
            # Save cropped face / best evidence crop
            face_crop_filename = f"track_{track_id}_face.jpg"
            full_frame_filename = f"track_{track_id}_full.jpg"
            
            face_crop_path = os.path.join(self.output_dir, face_crop_filename)
            full_frame_path = os.path.join(self.output_dir, full_frame_filename)

            # Draw visual evidence bounding boxes on the full frame
            annotated_frame = data["best_full_frame"].copy()
            px1, py1, px2, py2 = data["best_person_bbox"]
            cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), (16, 185, 129), 2) # Emerald person bbox
            
            # Label banner
            label = f"ID #{track_id} | Score: {data['best_score']}%"
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

            if data["best_face_bbox"]:
                fx1, fy1, fx2, fy2 = data["best_face_bbox"]
                cv2.rectangle(annotated_frame, (fx1, fy1), (fx2, fy2), (6, 182, 212), 2) # Cyan face bbox

            cv2.imwrite(full_frame_path, annotated_frame)

            # Save best face/head crop
            if data["best_face_crop"] is not None and data["best_face_crop"].size > 0:
                cv2.imwrite(face_crop_path, data["best_face_crop"])
            else:
                # Fallback to person crop if face crop wasn't saved
                person_crop = data["best_full_frame"][py1:py2, px1:px2]
                cv2.imwrite(face_crop_path, person_crop)

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
                "average_score": avg_score,
                "quality": data["best_quality"],
                "person_bbox": data["best_person_bbox"],
                "face_bbox": data["best_face_bbox"],
                "face_image_url": f"{relative_url_prefix}/{face_crop_filename}".replace("//", "/"),
                "full_frame_url": f"{relative_url_prefix}/{full_frame_filename}".replace("//", "/")
            }
            finalized_tracks.append(clean_summary)

        # Sort tracks by highest quality score first
        finalized_tracks.sort(key=lambda x: x["best_score"], reverse=True)
        return finalized_tracks
