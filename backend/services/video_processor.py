import os
import time
import json
import cv2
from typing import Dict, Any, Callable, Optional, List
import config
from services.person_detector import PersonDetector
from services.face_detector import FaceDetector
from services.face_quality import FaceQualityAssessor
from services.best_frame import BestFrameSelector

# Global singleton detectors
_GLOBAL_PERSON_DETECTOR: Optional[PersonDetector] = None
_GLOBAL_FACE_DETECTOR: Optional[FaceDetector] = None
_GLOBAL_QUALITY_ASSESSOR: Optional[FaceQualityAssessor] = None

def get_shared_detectors():
    global _GLOBAL_PERSON_DETECTOR, _GLOBAL_FACE_DETECTOR, _GLOBAL_QUALITY_ASSESSOR
    if _GLOBAL_PERSON_DETECTOR is None:
        _GLOBAL_PERSON_DETECTOR = PersonDetector(
            model_name=config.PERSON_MODEL_NAME,
            confidence_threshold=config.PERSON_CONFIDENCE_THRESHOLD,
            imgsz=config.PERSON_IMGSZ
        )
    if _GLOBAL_FACE_DETECTOR is None:
        _GLOBAL_FACE_DETECTOR = FaceDetector(score_threshold=config.YUNET_SCORE_THRESHOLD)
    if _GLOBAL_QUALITY_ASSESSOR is None:
        _GLOBAL_QUALITY_ASSESSOR = FaceQualityAssessor()
    return _GLOBAL_PERSON_DETECTOR, _GLOBAL_FACE_DETECTOR, _GLOBAL_QUALITY_ASSESSOR

class VideoProcessor:
    """
    Master video processing pipeline coordinating:
      - YOLOv8 Person Detection & ByteTrack Object Tracking
      - YuNet Facial Landmark Localization & SFace Feature Extraction
      - Quality v2 Multi-Metric Evaluation & Adaptive CLAHE Enhancement
      - Spatial Trajectory Tracking & Optimal Best-Frame / Runner-Up Isolation
      - First-Frame Thumbnail Generation for ATM Zone Layouts
    """
    def __init__(self, confidence_threshold: Optional[float] = None):
        self.person_detector, self.face_detector, self.quality_assessor = get_shared_detectors()
        if confidence_threshold is not None:
            self.person_detector.confidence_threshold = confidence_threshold

    def process_video(
        self,
        video_path: str,
        output_dir: str,
        task_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        atm_id: str = "ATM_CENTRAL_01",
        location_name: str = "Central Branch Kiosk",
        base_timestamp: Optional[str] = None,
        target_time_s: Optional[float] = None,
        window_margin_s: float = config.TARGET_WINDOW_DEFAULT_MARGIN_S
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
        duration = round(total_frames / fps, 2) if fps > 0 else 0.0

        # Handle targeted transaction window (e.g., +- 60s around transaction time)
        window_start_s: Optional[float] = None
        window_end_s: Optional[float] = None
        start_frame = 0
        target_total_frames = total_frames

        if target_time_s is not None and target_time_s >= 0:
            window_start_s = max(0.0, float(target_time_s) - float(window_margin_s))
            window_end_s = min(duration, float(target_time_s) + float(window_margin_s))
            start_frame = max(0, int(window_start_s * fps))
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            frame_idx = start_frame
            target_total_frames = max(1, int((window_end_s - window_start_s) * fps))
        else:
            frame_idx = 0

        # Dynamic stride for fast processing and scaling to long duration footage
        if target_total_frames > 15000:
            frame_stride = 12
        elif target_total_frames > 5000:
            frame_stride = 8
        elif target_total_frames > 1200:
            frame_stride = config.STRIDE_LONG
        elif target_total_frames > 400:
            frame_stride = config.STRIDE_MEDIUM
        else:
            frame_stride = config.STRIDE_SHORT

        # Reset ByteTrack temporal tracking state before each video (T0.3)
        self.person_detector.reset_tracker()

        selector = BestFrameSelector(output_dir=output_dir)
        thumbnail_saved = False
        thumbnail_filename = "thumbnail.jpg"
        thumbnail_path = os.path.join(output_dir, thumbnail_filename)

        start_time = time.time()
        processed_frames_count = 0
        total_detections_count = 0

        # Registry for collected face embeddings: {track_id: list of float}
        track_embeddings: Dict[int, List[float]] = {}

        # Initial progress broadcast
        if progress_callback:
            progress_callback({
                "task_id": task_id,
                "status": "processing",
                "progress": 2.0,
                "current_frame": frame_idx,
                "total_frames": target_total_frames,
                "processing_fps": 0.0,
                "tracks_count": 0
            })

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Save first valid frame as thumbnail for ATM ROI polygon definition
                if not thumbnail_saved:
                    cv2.imwrite(thumbnail_path, frame)
                    thumbnail_saved = True

                timestamp_sec = round(frame_idx / fps, 2)
                # Check if we passed the targeted transaction window
                if window_end_s is not None and timestamp_sec > window_end_s:
                    break

                if (frame_idx - start_frame) % frame_stride == 0:
                    # 1. Detect and track persons
                    detections = self.person_detector.track(frame, persist=True)
                    total_detections_count += len(detections)

                    # 2. Extract biometric evidence for each track
                    for det in detections:
                        track_id = det["track_id"]
                        person_bbox = det["bbox"]

                        face_info = self.face_detector.detect_face_in_person(frame, person_bbox)
                        has_real_face = bool(face_info.get("has_real_face", False)) if face_info else False
                        landmarks = face_info.get("landmarks", []) if face_info else []
                        det_conf = face_info.get("confidence", 0.0) if face_info else 0.0

                        # Save embedding if available
                        if face_info and face_info.get("embedding"):
                            track_embeddings[track_id] = face_info["embedding"]

                        if face_info and face_info.get("face_crop") is not None:
                            quality = self.quality_assessor.assess_crop(
                                face_info["face_crop"],
                                has_real_face=has_real_face,
                                landmarks=landmarks,
                                detector_conf=det_conf
                            )
                        else:
                            px1, py1, px2, py2 = person_bbox
                            fallback_crop = frame[py1:py2, px1:px2]
                            quality = self.quality_assessor.assess_crop(
                                fallback_crop,
                                has_real_face=False,
                                landmarks=[],
                                detector_conf=0.0
                            )

                        # 3. Update candidate and trajectory
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

                    # Periodic memory cleanup for long videos
                    if processed_frames_count % 250 == 0:
                        import gc
                        gc.collect()

                    # Send smooth real-time progress updates every 2 sampled frames
                    if progress_callback and (processed_frames_count % 2 == 0 or (frame_idx - start_frame) >= target_total_frames - frame_stride):
                        if window_start_s is not None:
                            progress_ratio = (frame_idx - start_frame) / max(1, target_total_frames)
                        else:
                            progress_ratio = frame_idx / max(1, total_frames)
                        pct = min(99.0, max(2.0, round(progress_ratio * 100, 1)))
                        elapsed = time.time() - start_time
                        curr_fps = round(processed_frames_count / max(0.001, elapsed), 1)
                        progress_callback({
                            "task_id": task_id,
                            "status": "processing",
                            "progress": pct,
                            "current_frame": frame_idx,
                            "total_frames": target_total_frames,
                            "processing_fps": curr_fps,
                            "tracks_count": len(selector.tracks)
                        })

                frame_idx += 1

        finally:
            cap.release()

        # Finalize evidence crops, deblurred images, and multi-angle composites
        relative_url_prefix = f"/results/{task_id}"
        tracks_summary = selector.finalize(relative_url_prefix=relative_url_prefix)

        # Attach face embeddings and save to embeddings registry
        if track_embeddings:
            embeddings_file = os.path.join(output_dir, "embeddings.json")
            with open(embeddings_file, "w") as f:
                json.dump(track_embeddings, f)

        # Automatically index faces into SQLite evidence_faces table
        import db
        import datetime
        for t in tracks_summary:
            tid = t["track_id"]
            str_tid = str(tid)
            emb = track_embeddings.get(tid) or track_embeddings.get(str_tid)
            if emb:
                ts = t.get("best_timestamp", 0.0)
                wall_clock = None
                if base_timestamp:
                    try:
                        base_dt = datetime.datetime.fromisoformat(base_timestamp.replace("Z", "+00:00"))
                        wall_clock = (base_dt + datetime.timedelta(seconds=ts)).isoformat()
                    except Exception:
                        wall_clock = None
                if not wall_clock:
                    wall_clock = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                db.save_evidence_face(
                    task_id=task_id,
                    track_id=tid,
                    atm_id=atm_id,
                    location_name=location_name,
                    timestamp_s=ts,
                    wall_clock_time=wall_clock,
                    face_image_url=t.get("face_image_url"),
                    full_frame_url=t.get("full_frame_url"),
                    enhanced_image_url=t.get("enhanced_image_url"),
                    composite_image_url=t.get("composite_image_url"),
                    quality_score=t.get("best_score", 0.0),
                    has_real_face=t.get("has_real_face", True),
                    embedding=emb
                )

        elapsed_total = round(time.time() - start_time, 2)
        avg_quality = (
            round(sum(t["best_score"] for t in tracks_summary) / len(tracks_summary), 1)
            if tracks_summary else 0.0
        )
        high_quality_count = sum(1 for t in tracks_summary if t["best_score"] >= 65.0)

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
                "elapsed_time_sec": elapsed_total,
                "thumbnail_url": f"{relative_url_prefix}/{thumbnail_filename}",
                "atm_id": atm_id,
                "location_name": location_name,
                "base_timestamp": base_timestamp,
                "target_time_s": target_time_s,
                "window_start_s": window_start_s,
                "window_end_s": window_end_s
            },
            "summary": {
                "unique_persons_tracked": len(tracks_summary),
                "total_detections": total_detections_count,
                "average_best_quality": avg_quality,
                "high_quality_evidence_count": high_quality_count
            },
            "tracks": tracks_summary
        }

        # Save results JSON
        results_json_path = os.path.join(output_dir, "results.json")
        with open(results_json_path, "w") as f:
            json.dump(result_payload, f, indent=2)

        if progress_callback:
            progress_callback({
                "task_id": task_id,
                "status": "completed",
                "progress": 100.0,
                "result": result_payload
            })

        return result_payload
