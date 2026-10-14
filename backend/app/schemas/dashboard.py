from typing import List, Optional
from pydantic import BaseModel

class AdminStatsResponse(BaseModel):
    total_cameras: int
    online_cameras: int
    videos_processed: int
    people_detected: int
    evidence_generated: int
    average_face_quality: float
    processing_time_seconds: float
    storage_usage_bytes: int
    total_alerts: int = 0
    unacknowledged_alerts: int = 0

class LegacyStatsResponse(BaseModel):
    total_videos_analyzed: int = 0
    total_persons_tracked: int = 0
    high_quality_evidence_captured: int = 0
    system_average_fidelity: float = 78.4
    active_models: List[str] = ["YOLOv8-Tracking", "Cascade-Biometrics", "Laplacian-Fidelity-v2"]
    total_processed_videos: Optional[int] = None
    total_persons_detected: Optional[int] = None
    avg_face_quality: Optional[float] = None
    storage_used_mb: Optional[float] = None
    active_cameras: Optional[int] = None
    system_uptime: Optional[str] = "99.98%"

    def model_post_init(self, __context):
        if self.total_processed_videos is not None:
            self.total_videos_analyzed = self.total_processed_videos
        if self.total_persons_detected is not None:
            self.total_persons_tracked = self.total_persons_detected
        if self.avg_face_quality is not None:
            self.system_average_fidelity = self.avg_face_quality
