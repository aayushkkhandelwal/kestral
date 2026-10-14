import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.evidence import EvidenceResponse

class PersonTrackBase(BaseModel):
    person_number: int
    start_frame: int = 0
    end_frame: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_frames: int = 0

class PersonTrackResponse(PersonTrackBase):
    track_id: uuid.UUID
    video_id: uuid.UUID
    best_evidence_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PersonTrackDetailResponse(PersonTrackResponse):
    best_evidence: Optional[EvidenceResponse] = None
    all_evidence: List[EvidenceResponse] = []
