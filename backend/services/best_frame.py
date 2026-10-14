import os
from typing import Dict, Any, List, Optional
import cv2
import numpy as np
import config

class BestFrameSelector:
    """
    Manages identity tracks across video sequences, records spatial trajectories,
    and isolates the single highest quality evidence frame as well as up to 4 runner-up
    frames separated temporally per tracked individual.
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
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
        face_crop = face_info.get("face_crop") if face_info else None
        face_bbox = face_info.get("bbox") if face_info else None

        if track_id not in self.tracks:
            self.tracks[track_id] = {
                "track_id": track_id,
                "first_seen_frame": frame_idx,
                "last_seen_frame": frame_idx,
                "first_seen_time": timestamp_sec,
                "last_seen_time": timestamp_sec,
                "total_detections": 1,
                "trajectory": [[timestamp_sec, person_bbox[0], person_bbox[1], person_bbox[2], person_bbox[3]]],
                "candidates": [{
                    "frame_idx": frame_idx,
                    "timestamp": timestamp_sec,
                    "score": score,
                    "has_real_face": has_real_face,
                    "person_bbox": person_bbox,
                    "face_bbox": face_bbox,
                    "quality": quality_metrics,
                    "face_crop": face_crop.copy() if face_crop is not None else None,
                    "full_frame": full_frame.copy()
                }],
                "all_scores": [score]
            }
        else:
            t = self.tracks[track_id]
            t["last_seen_frame"] = frame_idx
            t["last_seen_time"] = timestamp_sec
            t["total_detections"] += 1
            t["trajectory"].append([timestamp_sec, person_bbox[0], person_bbox[1], person_bbox[2], person_bbox[3]])
            t["all_scores"].append(score)

            t["candidates"].append({
                "frame_idx": frame_idx,
                "timestamp": timestamp_sec,
                "score": score,
                "has_real_face": has_real_face,
                "person_bbox": person_bbox,
                "face_bbox": face_bbox,
                "quality": quality_metrics,
                "face_crop": face_crop.copy() if face_crop is not None else None,
                "full_frame": full_frame.copy()
            })

    def _select_best_and_runner_ups(self, candidates: List[Dict[str, Any]]) -> (Dict[str, Any], List[Dict[str, Any]]):
        if not candidates:
            return None, []

        # 1. Apply light 3-point temporal moving average smoothing to scores
        smoothed_scores = []
        for i in range(len(candidates)):
            window = [candidates[j]["score"] for j in range(max(0, i - 1), min(len(candidates), i + 2))]
            smoothed_scores.append(float(np.mean(window)))

        scored_candidates = []
        for i, c in enumerate(candidates):
            sc = dict(c)
            sc["smoothed_score"] = smoothed_scores[i]
            scored_candidates.append(sc)

        # 2. Sort: primary sort has_real_face descending, secondary sort smoothed_score descending
        scored_candidates.sort(key=lambda x: (x["has_real_face"], x["smoothed_score"]), reverse=True)

        best_candidate = scored_candidates[0]
        selected_runner_ups: List[Dict[str, Any]] = []

        # 3. Select runner-ups separated by at least MIN_RUNNER_UP_INTERVAL_SEC
        for cand in scored_candidates[1:]:
            if len(selected_runner_ups) >= config.MAX_RUNNER_UPS:
                break

            # Check temporal separation from best candidate and all already picked runner-ups
            ts = cand["timestamp"]
            diff_from_best = abs(ts - best_candidate["timestamp"])
            if diff_from_best < config.MIN_RUNNER_UP_INTERVAL_SEC:
                continue

            diff_from_others = all(
                abs(ts - ru["timestamp"]) >= config.MIN_RUNNER_UP_INTERVAL_SEC
                for ru in selected_runner_ups
            )
            if diff_from_others:
                selected_runner_ups.append(cand)

        return best_candidate, selected_runner_ups

    def finalize(self, relative_url_prefix: str = "") -> List[Dict[str, Any]]:
        finalized_tracks: List[Dict[str, Any]] = []

        for track_id, data in self.tracks.items():
            candidates = data.get("candidates", [])
            best_cand, runner_ups = self._select_best_and_runner_ups(candidates)
            if best_cand is None:
                continue

            face_crop_filename = f"track_{track_id}_face.jpg"
            full_frame_filename = f"track_{track_id}_full.jpg"

            face_crop_path = os.path.join(self.output_dir, face_crop_filename)
            full_frame_path = os.path.join(self.output_dir, full_frame_filename)

            # 1. Save annotated full frame
            annotated_frame = best_cand["full_frame"].copy()
            px1, py1, px2, py2 = best_cand["person_bbox"]
            cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), (16, 185, 129), 2)  # Emerald

            has_face = best_cand.get("has_real_face", False)
            label = f"ID #{track_id} | Score: {best_cand['score']:.1f}"
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

            if best_cand["face_bbox"] and has_face:
                fx1, fy1, fx2, fy2 = best_cand["face_bbox"]
                cv2.rectangle(annotated_frame, (fx1, fy1), (fx2, fy2), (6, 182, 212), 2)  # Cyan face bbox

            cv2.imwrite(full_frame_path, annotated_frame)

            # 2. Save best face crop
            if best_cand["face_crop"] is not None and best_cand["face_crop"].size > 0:
                cv2.imwrite(face_crop_path, best_cand["face_crop"])
            else:
                person_crop = best_cand["full_frame"][py1:py2, px1:px2]
                cv2.imwrite(face_crop_path, person_crop)

            # 3. Save runner-ups crops
            runner_ups_payload: List[Dict[str, Any]] = []
            for k, ru in enumerate(runner_ups):
                alt_filename = f"track_{track_id}_alt{k + 1}.jpg"
                alt_path = os.path.join(self.output_dir, alt_filename)
                
                ru_crop = ru.get("face_crop")
                if ru_crop is not None and ru_crop.size > 0:
                    cv2.imwrite(alt_path, ru_crop)
                else:
                    rx1, ry1, rx2, ry2 = ru["person_bbox"]
                    cv2.imwrite(alt_path, ru["full_frame"][ry1:ry2, rx1:rx2])

                runner_ups_payload.append({
                    "frame_idx": ru["frame_idx"],
                    "timestamp": round(ru["timestamp"], 2),
                    "score": round(ru["score"], 1),
                    "face_image_url": f"{relative_url_prefix}/{alt_filename}".replace("//", "/")
                })

            duration = round(data["last_seen_time"] - data["first_seen_time"], 2)
            avg_score = round(float(np.mean(data["all_scores"])), 1) if data["all_scores"] else 0.0

            clean_summary = {
                # Existing keys (Additive only - keep backwards compatibility)
                "track_id": track_id,
                "first_seen_time": round(data["first_seen_time"], 2),
                "last_seen_time": round(data["last_seen_time"], 2),
                "duration_seconds": duration,
                "total_detections": data["total_detections"],
                "best_frame_idx": best_cand["frame_idx"],
                "best_timestamp": round(best_cand["timestamp"], 2),
                "best_score": best_cand["score"],
                "has_real_face": has_face,
                "average_score": avg_score,
                "quality": best_cand["quality"],
                "person_bbox": best_cand["person_bbox"],
                "face_bbox": best_cand["face_bbox"],
                "face_image_url": f"{relative_url_prefix}/{face_crop_filename}".replace("//", "/"),
                "full_frame_url": f"{relative_url_prefix}/{full_frame_filename}".replace("//", "/"),
                # New keys per CONTRACTS section B
                "trajectory": data.get("trajectory", []),
                "runner_ups": runner_ups_payload
            }
            finalized_tracks.append(clean_summary)

        # Sort: verified faces first, then by score descending
        finalized_tracks.sort(key=lambda x: (x["has_real_face"], x["best_score"]), reverse=True)
        return finalized_tracks
