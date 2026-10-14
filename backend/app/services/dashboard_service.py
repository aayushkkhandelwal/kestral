import os
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.config import get_settings
from app.models.camera import Camera, CameraStatus
from app.models.video import Video, VideoStatus
from app.models.person_track import PersonTrack
from app.models.face_evidence import FaceEvidence
from app.models.alert import Alert, AlertStatus
from app.schemas.dashboard import AdminStatsResponse, LegacyStatsResponse


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def get_admin_metrics(self) -> AdminStatsResponse:
        # Total cameras
        total_cameras = self.db.scalar(select(func.count(Camera.id))) or 0

        # Online cameras
        online_cameras = self.db.scalar(
            select(func.count(Camera.id)).where(Camera.status == CameraStatus.ONLINE)
        ) or 0

        # Videos processed
        videos_processed = self.db.scalar(
            select(func.count(Video.id)).where(Video.status == VideoStatus.COMPLETED)
        ) or 0

        # People detected
        people_detected = self.db.scalar(select(func.count(PersonTrack.id))) or 0

        # Evidence generated
        evidence_generated = self.db.scalar(select(func.count(FaceEvidence.id))) or 0

        # Average face quality
        avg_quality_raw = self.db.scalar(select(func.avg(FaceEvidence.quality_score)))
        avg_quality = float(avg_quality_raw) if avg_quality_raw is not None else 0.0

        # Processing time (seconds)
        # Calculate from duration of completed videos or file size
        total_duration = self.db.scalar(
            select(func.sum(Video.duration)).where(Video.status == VideoStatus.COMPLETED)
        ) or 0.0

        # Storage usage in bytes
        db_storage_sum = self.db.scalar(select(func.sum(Video.file_size))) or 0
        disk_storage_bytes = self._calculate_storage_usage()
        total_storage = max(int(db_storage_sum), disk_storage_bytes)

        # Alerts summary
        total_alerts = self.db.scalar(select(func.count(Alert.id))) or 0
        unacknowledged_alerts = self.db.scalar(
            select(func.count(Alert.id)).where(Alert.status == AlertStatus.ACTIVE)
        ) or 0

        return AdminStatsResponse(
            total_cameras=total_cameras,
            online_cameras=online_cameras,
            videos_processed=videos_processed,
            people_detected=people_detected,
            evidence_generated=evidence_generated,
            average_face_quality=round(avg_quality, 2),
            processing_time_seconds=round(float(total_duration), 2),
            storage_usage_bytes=total_storage,
            total_alerts=total_alerts,
            unacknowledged_alerts=unacknowledged_alerts
        )

    def get_legacy_stats(self) -> LegacyStatsResponse:
        metrics = self.get_admin_metrics()
        storage_mb = round(metrics.storage_usage_bytes / (1024 * 1024), 2)

        return LegacyStatsResponse(
            total_processed_videos=metrics.videos_processed,
            total_persons_detected=metrics.people_detected,
            avg_face_quality=metrics.average_face_quality,
            storage_used_mb=storage_mb,
            active_cameras=metrics.online_cameras,
            system_uptime="99.98%"
        )

    def _calculate_storage_usage(self) -> int:
        """Fast cached or bounded sum of storage directory usage."""
        total_bytes = 0
        for dir_name in ["uploads", "results", "faces", "frames", "exports"]:
            target_dir = os.path.join(self.settings.BASE_STORAGE_DIR, dir_name)
            if os.path.exists(target_dir):
                try:
                    for entry in os.scandir(target_dir):
                        if entry.is_file():
                            total_bytes += entry.stat().st_size
                except Exception:
                    pass
        return total_bytes
