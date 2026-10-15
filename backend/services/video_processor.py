import os
import time
import json
from datetime import datetime
import cv2
from typing import Dict, Any, Callable, Optional
from services.person_detector import PersonDetector
from services.face_detector import FaceDetector
from services.face_quality import FaceQualityAssessor
from services.best_frame import BestFrameSelector

# Global singleton detectors to avoid re-initializing weights on every upload
_GLOBAL_PERSON_DETECTOR: Optional[PersonDetector] = None
_GLOBAL_FACE_DETECTOR: Optional[FaceDetector] = None
_GLOBAL_QUALITY_ASSESSOR: Optional[FaceQualityAssessor] = None

def get_shared_detectors():
    global _GLOBAL_PERSON_DETECTOR, _GLOBAL_FACE_DETECTOR, _GLOBAL_QUALITY_ASSESSOR
    if _GLOBAL_PERSON_DETECTOR is None:
        _GLOBAL_PERSON_DETECTOR = PersonDetector(confidence_threshold=0.35)
    if _GLOBAL_FACE_DETECTOR is None:
        _GLOBAL_FACE_DETECTOR = FaceDetector()
    if _GLOBAL_QUALITY_ASSESSOR is None:
        _GLOBAL_QUALITY_ASSESSOR = FaceQualityAssessor()
    return _GLOBAL_PERSON_DETECTOR, _GLOBAL_FACE_DETECTOR, _GLOBAL_QUALITY_ASSESSOR

class VideoProcessor:
    """
    High-performance video processing pipeline for multi-object tracking,
    biometric face isolation, and evidence capture.
    """
    def __init__(self, confidence_threshold: float = 0.35):
        self.person_detector, self.face_detector, self.quality_assessor = get_shared_detectors()

    def process_video(
        self,
        video_path: str,
        output_dir: str,
        task_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        os.makedirs(output_dir, exist_ok=True)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if total_frames <= 0 or width <= 0 or height <= 0:
            cap.release()
            raise ValueError(f"Video file contains no valid decodable frames (frames={total_frames}, dimensions={width}x{height})")

        duration = round(total_frames / fps, 2) if fps > 0 else 0.0

        # Dynamic stride for fast, responsive forensic processing:
        # short clips (<400 frames, ~15s): stride 3 (~8-10 fps analysis)
        # medium clips (400-1500 frames, ~15-50s): stride 5 (~5-6 fps analysis)
        # long surveillance videos (1500-3500 frames, ~1-2 min): stride 8 (~3.5 fps analysis)
        # very long surveillance videos (>3500 frames, 2+ min): stride 10 (~3 fps analysis)
        if total_frames > 3500:
            frame_stride = 10
        elif total_frames > 1500:
            frame_stride = 8
        elif total_frames > 400:
            frame_stride = 5
        else:
            frame_stride = 3

        selector = BestFrameSelector(output_dir=output_dir)

        start_time = time.time()
        frame_idx = 0
        processed_frames_count = 0
        total_detections_count = 0

        # Initial progress broadcast
        if progress_callback:
            progress_callback({
                "task_id": task_id,
                "status": "processing",
                "progress": 2.0,
                "current_frame": 0,
                "total_frames": total_frames,
                "processing_fps": 0.0,
                "tracks_count": 0
            })

        try:
            while True:
                # Fast frame grabbing: skip expensive full decoding of intermediate frames
                if frame_idx % frame_stride != 0:
                    ret = cap.grab()
                    if not ret:
                        break
                    frame_idx += 1
                    continue

                ret, frame = cap.read()
                if not ret:
                    break

                timestamp_sec = round(frame_idx / fps, 2)

                # 1. Detect and track persons
                detections = self.person_detector.track(frame, persist=True)
                total_detections_count += len(detections)

                # 2. Extract biometric evidence for each track
                for det in detections:
                    track_id = det["track_id"]
                    person_bbox = det["bbox"]

                    face_info = self.face_detector.detect_face_in_person(frame, person_bbox)
                    has_real_face = bool(face_info.get("has_real_face", False)) if face_info else False

                    if face_info and face_info.get("face_crop") is not None:
                        quality = self.quality_assessor.assess_crop(
                            face_info["face_crop"],
                            has_real_face=has_real_face
                        )
                    else:
                        px1, py1, px2, py2 = person_bbox
                        fallback_crop = frame[py1:py2, px1:px2]
                        quality = self.quality_assessor.assess_crop(fallback_crop, has_real_face=False)

                    # 3. Update best candidate
                    selector.update_track(
                        track_id=track_id,
                        frame_idx=frame_idx,
                        timestamp_sec=timestamp_sec,
                        full_frame=frame,
                        person_bbox=person_bbox,
                        face_info=face_info,
                        quality_metrics=quality
                    )

                processed_frames_count += 1

                # Send smooth real-time progress updates every 2 sampled frames
                if progress_callback and (processed_frames_count % 2 == 0 or frame_idx >= total_frames - frame_stride):
                    pct = min(99.0, max(2.0, round((frame_idx / max(1, total_frames)) * 100, 1)))
                    elapsed = time.time() - start_time
                    curr_fps = round(frame_idx / max(0.001, elapsed), 1)
                    progress_callback({
                        "task_id": task_id,
                        "status": "processing",
                        "progress": pct,
                        "current_frame": frame_idx,
                        "total_frames": total_frames,
                        "processing_fps": curr_fps,
                        "tracks_count": len(selector.tracks)
                    })

                frame_idx += 1

        finally:
            cap.release()

        # Update progress so UI knows decoding is complete and post-processing has begun
        if progress_callback:
            progress_callback({
                "task_id": task_id,
                "status": "processing",
                "progress": 99.2,
                "current_frame": total_frames,
                "total_frames": total_frames,
                "processing_fps": 0.0,
                "tracks_count": len(selector.tracks)
            })

        # Finalize evidence crops & consolidate identities
        relative_url_prefix = f"/results/{task_id}"
        tracks_summary = selector.finalize(relative_url_prefix=relative_url_prefix)

        if progress_callback:
            progress_callback({
                "task_id": task_id,
                "status": "processing",
                "progress": 99.7,
                "current_frame": total_frames,
                "total_frames": total_frames,
                "processing_fps": 0.0,
                "tracks_count": len(tracks_summary)
            })

        elapsed_total = round(time.time() - start_time, 2)
        avg_quality = (
            round(sum(t["best_score"] for t in tracks_summary) / len(tracks_summary), 1)
            if tracks_summary else 0.0
        )
        high_quality_count = sum(1 for t in tracks_summary if t["best_score"] >= 65.0)

        # Compute input video hash and build evidence manifest
        video_hash = selector._compute_sha256(video_path)
        video_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0

        evidence_files_list = []
        for t in tracks_summary:
            if t.get("face_sha256"):
                evidence_files_list.append({
                    "filename": f"track_{t['track_id']}_face.jpg",
                    "url": t.get("face_image_url"),
                    "sha256": t.get("face_sha256")
                })
            if t.get("full_frame_sha256"):
                evidence_files_list.append({
                    "filename": f"track_{t['track_id']}_full.jpg",
                    "url": t.get("full_frame_url"),
                    "sha256": t.get("full_frame_sha256")
                })

        integrity_manifest = {
            "original_video": {
                "file_path": video_path,
                "size_bytes": video_size,
                "sha256": video_hash
            },
            "evidence_files": evidence_files_list,
            "processed_timestamp": datetime.utcnow().isoformat() + "Z",
            "models_used": {
                "person_detector": "YOLOv8n (Ultralytics)",
                "face_detector": "OpenCV YuNet ONNX (5 landmarks)",
                "quality_assessor": "Laplacian-40/Res-30/Lum-15/Contrast-15"
            },
            "disclaimer": "SHA-256 cryptographic hashes detect subsequent modification or corruption but do not independently establish source authenticity or chain-of-custody."
        }

        result_payload = {
            "task_id": task_id,
            "status": "completed",
            "progress": 100.0,
            "metadata": {
                "total_frames": total_frames,
                "fps": round(fps, 2),
                "resolution": f"{width}x{height}",
                "duration_seconds": duration,
                "frames_processed": processed_frames_count,
                "elapsed_time_sec": elapsed_total
            },
            "summary": {
                "unique_persons_tracked": len(tracks_summary),
                "total_detections": total_detections_count,
                "average_best_quality": avg_quality,
                "high_quality_evidence_count": high_quality_count
            },
            "tracks": tracks_summary,
            "integrity": integrity_manifest
        }

        # Save results JSON
        results_json_path = os.path.join(output_dir, "results.json")
        with open(results_json_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)

        if progress_callback:
            progress_callback({
                "task_id": task_id,
                "status": "completed",
                "progress": 100.0,
                "result": result_payload
            })

        return result_payload
