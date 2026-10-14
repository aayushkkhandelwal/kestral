import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ClipResponse(BaseModel):
    clip_id: uuid.UUID
    event_id: uuid.UUID
    video_id: Optional[uuid.UUID] = None
    clip_path: str
    clip_start_sec: float
    clip_end_sec: float
    pre_event_duration: float
    post_event_duration: float
    sha256: Optional[str] = None
    file_size_bytes: int
    export_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreenshotCreate(BaseModel):
    video_timestamp_sec: float = Field(..., ge=0.0)
    frame_number: int = Field(0, ge=0)
    notes: Optional[str] = None
    image_base64: Optional[str] = None  # Optional client-side snapshot data


class ScreenshotResponse(BaseModel):
    screenshot_id: uuid.UUID
    event_id: Optional[uuid.UUID] = None
    video_id: Optional[uuid.UUID] = None
    camera_id: Optional[uuid.UUID] = None
    image_path: str
    video_timestamp_sec: float
    frame_number: int
    sha256: Optional[str] = None
    dimensions: str
    notes: Optional[str] = None
    captured_at_utc: datetime

    model_config = ConfigDict(from_attributes=True)


class SurveillanceEventCreate(BaseModel):
    event_type: str = Field(..., pattern="^(person_entry|person_exit|transaction_start|loitering|inferred_transaction)$")
    camera_id: Optional[uuid.UUID] = None
    video_id: Optional[uuid.UUID] = None
    track_id: Optional[uuid.UUID] = None
    zone_id: Optional[uuid.UUID] = None
    person_number: Optional[int] = None
    zone_name: Optional[str] = None
    video_timestamp_sec: float
    source_frame: int = 0
    confidence: float = 1.0
    source: str = "vision_analytics"
    event_metadata: Optional[Dict[str, Any]] = None


class SurveillanceEventResponse(BaseModel):
    event_id: uuid.UUID
    camera_id: Optional[uuid.UUID] = None
    video_id: Optional[uuid.UUID] = None
    track_id: Optional[uuid.UUID] = None
    zone_id: Optional[uuid.UUID] = None
    event_type: str
    event_timestamp_utc: datetime
    video_timestamp_sec: float
    source_frame: int
    person_number: Optional[int] = None
    zone_name: Optional[str] = None
    confidence: float
    source: str
    event_metadata: Optional[Dict[str, Any]] = None
    processing_status: str
    created_at: datetime

    clip: Optional[ClipResponse] = None
    screenshots: Optional[List[ScreenshotResponse]] = []

    model_config = ConfigDict(from_attributes=True)


class TransactionWebhookPayload(BaseModel):
    atm_id: str
    transaction_id: str
    event_type: str = "transaction_start"
    timestamp_utc: Optional[datetime] = None
    amount: Optional[float] = None
    card_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EvidenceExportRequest(BaseModel):
    event_ids: List[uuid.UUID] = Field(..., min_length=1)
    include_clips: bool = True
    include_screenshots: bool = True
    include_metadata_manifest: bool = True
    export_notes: Optional[str] = None


class EvidenceExportResponse(BaseModel):
    export_id: uuid.UUID
    export_filename: str
    download_url: str
    file_size_bytes: int
    sha256: str
    events_included_count: int
    created_at: datetime
