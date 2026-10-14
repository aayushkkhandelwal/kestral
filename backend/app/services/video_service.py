import os
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Tuple, BinaryIO, Dict, Any
from sqlalchemy.orm import Session
from app.models.video import Video, ProcessingStatus
from app.models.person_track import PersonTrack
from app.models.face_evidence import FaceEvidence, QualityGrade
from app.models.user import User
from app.repositories.video_repository import VideoRepository
from app.repositories.track_repository import TrackRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.audit_repository import AuditRepository
from app.core.exceptions import EntityNotFoundException, StorageException
from app.core.logging import logger
from app.core.config import get_settings
from app.utils.storage import StorageManager
from app.utils.hashing import compute_sha256_file
from app.ai.adapters import VisionPipelineAdapter

settings = get_settings()

# In-memory progress tracking for real-time frontend polling
ACTIVE_TASKS_TELEMETRY: Dict[str, Dict[str, Any]] = {}

class VideoService:
    def __init__(self, db: Session):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.track_repo = TrackRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.audit_repo = AuditRepository(db)
        self.ai_adapter = VisionPipelineAdapter(confidence_threshold=0.35)

    def upload_and_stage_video(
        self,
        file_obj: BinaryIO,
        original_filename: str,
        camera_id: Optional[uuid.UUID] = None,
        uploader: Optional[User] = None,
        request_id: Optional[str] = None
    ) -> Video:
        rel_path, safe_name, file_size, sha256_hash = StorageManager.save_upload_stream(
            file_obj=file_obj,
            original_filename=original_filename,
            max_bytes=settings.MAX_UPLOAD_SIZE_BYTES
        )

        video = Video(
            camera_id=camera_id,
            filename=safe_name,
            file_path=rel_path,
            file_size_bytes=file_size,
            sha256=sha256_hash,
            uploaded_by=uploader.id if uploader else None,
            processing_status=ProcessingStatus.QUEUED
        )
        self.video_repo.add(video)

        self.audit_repo.record_action(
            action="video.upload",
            resource="video",
            user_id=uploader.id if uploader else None,
            request_id=request_id,
            details={"video_id": str(video.video_id), "filename": safe_name, "sha256": sha256_hash}
        )
        self.db.commit()
        self.db.refresh(video)

        # Register in-memory telemetry for legacy polling endpoints
        task_id = str(video.video_id)[:8]
        ACTIVE_TASKS_TELEMETRY[task_id] = {
            "task_id": task_id,
            "video_id": str(video.video_id),
            "filename": safe_name,
            "video_url": f"/{rel_path}",
            "status": "queued",
            "progress": 0.0,
            "tracks_count": 0,
            "current_frame": 0,
            "total_frames": 0,
            "processing_fps": 0.0
        }

        return video

    def execute_video_processing(self, video_id: uuid.UUID, task_id: str) -> Dict[str, Any]:
        """
        Executes vision inference in background worker and persists all results
        (videos, tracks, face evidence) into PostgreSQL.
        """
        video = self.video_repo.get_by_id(video_id)
        if not video:
            raise EntityNotFoundException("Video", str(video_id))

        video.processing_status = ProcessingStatus.PROCESSING
        self.video_repo.add(video)
        self.db.commit()

        abs_video_path = os.path.join(settings.BASE_DIR, video.file_path)
        output_dir = os.path.join(settings.results_path, task_id)
        os.makedirs(output_dir, exist_ok=True)

        def on_progress(p: Dict[str, Any]):
            if task_id in ACTIVE_TASKS_TELEMETRY:
                ACTIVE_TASKS_TELEMETRY[task_id].update(p)

        try:
            results = self.ai_adapter.process_video_file(
                video_path=abs_video_path,
                output_dir=output_dir,
                task_id=task_id,
                progress_callback=on_progress
            )

            # 1. Update Video metadata
            metadata = results.get("metadata", {})
            video.duration = float(metadata.get("duration_seconds", 0.0))
            video.fps = float(metadata.get("fps", 0.0))
            video.resolution = str(metadata.get("resolution", "unknown"))
            video.processed_at = datetime.now(timezone.utc)
            video.processing_status = ProcessingStatus.COMPLETED
            self.video_repo.add(video)

            # 2. Persist Person Tracks and Face Evidence
            tracks_data = results.get("tracks", [])
            for t_item in tracks_data:
                person_num = int(t_item.get("track_id", 0))

                track = self.track_repo.get_by_video_and_person(video.video_id, person_num)
                if not track:
                    track = PersonTrack(
                        video_id=video.video_id,
                        person_number=person_num,
                        start_frame=int(t_item.get("best_frame_idx", 0)),
                        end_frame=int(t_item.get("best_frame_idx", 0)),
                        total_frames=int(t_item.get("total_detections", 1))
                    )
                    self.track_repo.add(track)
                    self.db.flush()

                # Build Face Evidence Record
                quality_score = float(t_item.get("quality_score", 0.0))
                sharpness = float(t_item.get("sharpness_score", 0.0))
                exposure = float(t_item.get("exposure_score", 0.0))
                face_conf = t_item.get("face_confidence")
                if face_conf is not None:
                    face_conf = float(face_conf)

                # Map Grade
                grade_str = str(t_item.get("quality", {}).get("grade", "C")).upper()
                try:
                    grade = QualityGrade(grade_str)
                except Exception:
                    grade = QualityGrade.C

                crop_url = str(t_item.get("crop_url", ""))
                full_frame_url = str(t_item.get("full_frame_url", ""))

                # Compute file hashes if files exist
                crop_path = os.path.join(settings.BASE_DIR, crop_url.lstrip("/"))
                full_path = os.path.join(settings.BASE_DIR, full_frame_url.lstrip("/"))
                sha_crop = compute_sha256_file(crop_path) if os.path.exists(crop_path) else None
                sha_frame = compute_sha256_file(full_path) if os.path.exists(full_path) else None

                evidence = FaceEvidence(
                    track_id=track.track_id,
                    face_crop_path=crop_url,
                    full_frame_path=full_frame_url,
                    quality_score=quality_score,
                    quality_grade=grade,
                    sharpness=sharpness,
                    brightness=exposure,
                    contrast=0.5,
                    resolution=f"{t_item.get('quality', {}).get('crop_width', 0)}x{t_item.get('quality', {}).get('crop_height', 0)}",
                    face_confidence=face_conf,
                    sha256_crop=sha_crop,
                    sha256_frame=sha_frame,
                    is_best=False
                )
                self.evidence_repo.add(evidence)
                self.db.flush()

                # Promote to best evidence atomically
                self.evidence_repo.promote_candidate_if_best(evidence)

            self.audit_repo.record_action(
                action="video.process.completed",
                resource="video",
                user_id=video.uploaded_by,
                details={"video_id": str(video.video_id), "task_id": task_id, "tracks_extracted": len(tracks_data)}
            )
            self.db.commit()

            ACTIVE_TASKS_TELEMETRY[task_id] = {
                "task_id": task_id,
                "video_id": str(video.video_id),
                "filename": video.filename,
                "status": "completed",
                "progress": 100.0,
                "result": results
            }

            return results
        except Exception as e:
            logger.error(f"Error processing video task {task_id}: {e}")
            video.processing_status = ProcessingStatus.FAILED
            self.video_repo.add(video)
            self.audit_repo.record_action(
                action="video.process.failed",
                resource="video",
                user_id=video.uploaded_by,
                details={"video_id": str(video.video_id), "task_id": task_id, "error": str(e)}
            )
            self.db.commit()

            ACTIVE_TASKS_TELEMETRY[task_id] = {
                "task_id": task_id,
                "video_id": str(video.video_id),
                "filename": video.filename,
                "status": "failed",
                "progress": 0.0,
                "error": str(e)
            }
            raise

    def get_video(self, video_id: uuid.UUID) -> Video:
        video = self.video_repo.get_by_id(video_id)
        if not video:
            raise EntityNotFoundException("Video", str(video_id))
        return video

    def search_videos(
        self,
        camera_id: Optional[uuid.UUID] = None,
        status: Optional[ProcessingStatus] = None,
        filename_query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[Video], int]:
        return self.video_repo.search_videos(
            camera_id=camera_id,
            status=status,
            filename_query=filename_query,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit
        )

    def delete_video(self, video_id: uuid.UUID, user: Optional[User] = None, request_id: Optional[str] = None) -> bool:
        video = self.get_video(video_id)
        # Delete file on disk
        StorageManager.delete_file(video.file_path)
        self.video_repo.delete(video)
        self.audit_repo.record_action(
            action="video.delete",
            resource="video",
            user_id=user.id if user else None,
            request_id=request_id,
            details={"video_id": str(video_id)}
        )
        self.db.commit()
        return True
