import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.face_evidence import QualityGrade

class EvidenceBase(BaseModel):
    face_crop_path: Optional[str] = None
    full_frame_path: str
    quality_score: float
    quality_grade: str
    sharpness: float
    brightness: float
    contrast: float
    resolution: str
    face_confidence: Optional[float] = None
    is_best: bool = False
    sha256_crop: Optional[str] = None
    sha256_frame: Optional[str] = None

class EvidenceResponse(EvidenceBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    evidence_id: uuid.UUID
    id: Optional[uuid.UUID] = Field(default=None)
    track_id: uuid.UUID
    created_at: datetime
    crop_url: Optional[str] = None
    full_frame_url: Optional[str] = None

    def model_post_init(self, __context):
        if self.id is None:
            self.id = self.evidence_id
        if not self.crop_url and self.face_crop_path:
            self.crop_url = f"/{self.face_crop_path.lstrip('/')}"
        if not self.full_frame_url and self.full_frame_path:
            self.full_frame_url = f"/{self.full_frame_path.lstrip('/')}"

class EvidenceSearchFilter(BaseModel):
    video_id: Optional[uuid.UUID] = None
    camera_id: Optional[uuid.UUID] = None
    track_id: Optional[uuid.UUID] = None
    case_id: Optional[uuid.UUID] = None
    is_best: Optional[bool] = None
    min_quality: Optional[float] = None
    max_quality: Optional[float] = None
    quality_grade: Optional[str] = None
    person_number: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 50

EvidenceFilter = EvidenceSearchFilter

class EvidenceExportRequest(BaseModel):
    case_id: Optional[uuid.UUID] = None
    evidence_ids: Optional[List[uuid.UUID]] = None
    min_quality_score: Optional[float] = None
    include_full_frames: bool = True

class IntegrityVerificationResponse(BaseModel):
    evidence_id: uuid.UUID
    face_crop_exists: bool
    full_frame_exists: bool
    face_hash_recorded: Optional[str] = None
    face_hash_current: Optional[str] = None
    face_hash_matches: bool
    frame_hash_recorded: Optional[str] = None
    frame_hash_current: Optional[str] = None
    frame_hash_matches: bool
    is_valid: bool
