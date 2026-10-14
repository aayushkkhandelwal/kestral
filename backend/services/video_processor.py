import os
import time
import json
import cv2
from typing import Dict, Any, Callable, Optional
from services.person_detector import PersonDetector
from services.face_detector import FaceDetector
from services.face_quality import FaceQualityAssessor
from services.best_frame import BestFrameSelector

class VideoProcessor:
    """
    Orchestrates the end-to-end video pipeline: frame decoding, YOLO tracking,
    face isolation, quality scoring, and best-frame extraction.
    """
    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence_threshold: float = 0.35,
        frame_stride: int = 2
    ):
        self.frame_stride = max(1, frame_stride)
        self.person_detector = PersonDetector(model_name=model_name, confidence_threshold=confidence_threshold)
        self.face_detector = FaceDetector()
        self.quality_assessor = FaceQualityAssessor()

    def process_video(
        self,
        video_path: str,
        output_dir: str,
        task_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes pipeline on the provided video file and writes evidence captures to output_dir.
        """
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

        selector = BestFrameSelector(output_dir=output_dir)

        start_time = time.time()
        frame_idx = 0
        processed_frames_count = 0
        total_detections_count = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Frame sampling stride
                if frame_idx % self.frame_stride == 0:
                    timestamp_sec = round(frame_idx / fps, 2)

                    # 1. Detect and track persons
                    detections = self.person_detector.track(frame, persist=True)
                    total_detections_count += len(detections)

                    # 2. For each tracked person, locate face and score quality
                    for det in detections:
                        track_id = det["track_id"]
                        person_bbox = det["bbox"]

                        face_info = self.face_detector.detect_face_in_person(frame, person_bbox)

                        if face_info and face_info.get("face_crop") is not None:
                            quality = self.quality_assessor.assess_crop(
                                face_info["face_crop"],
                                is_heuristic=face_info.get("is_heuristic", False)
                            )
                        else:
                            # Quality assess upper-body person crop as fallback
                            px1, py1, px2, py2 = person_bbox
                            fallback_crop = frame[py1:py2, px1:px2]
                            quality = self.quality_assessor.assess_crop(fallback_crop, is_heuristic=True)

                        # 3. Update track candidate
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

                    # Send progress updates every few frames
                    if progress_callback and (processed_frames_count % 3 == 0 or frame_idx >= total_frames - self.frame_stride):
                        pct = min(100, round((frame_idx / max(1, total_frames)) * 100, 1))
                        elapsed = time.time() - start_time
                        curr_fps = round(processed_frames_count / max(0.001, elapsed), 1)
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

        # Finalize and save best evidence frames
        relative_url_prefix = f"/results/{task_id}"
        tracks_summary = selector.finalize(relative_url_prefix=relative_url_prefix)

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
                "elapsed_time_sec": elapsed_total
            },
            "summary": {
                "unique_persons_tracked": len(tracks_summary),
                "total_detections": total_detections_count,
                "average_best_quality": avg_quality,
                "high_quality_evidence_count": high_quality_count
            },
            "tracks": tracks_summary
        }

        # Save results JSON into the task directory
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
