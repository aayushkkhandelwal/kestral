import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.video import ProcessingStatus

class VideoBase(BaseModel):
    filename: str
    duration: float = 0.0
    fps: float = 0.0
    resolution: str = "unknown"
    file_size_bytes: int = 0
    sha256: Optional[str] = None
    processing_status: str = "queued"

class VideoResponse(VideoBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    video_id: uuid.UUID
    id: Optional[uuid.UUID] = None
    camera_id: Optional[uuid.UUID] = None
    file_path: str
    storage_path: Optional[str] = None
    uploaded_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    def model_post_init(self, __context):
        if self.id is None:
            self.id = self.video_id
        if self.storage_path is None:
            self.storage_path = self.file_path

class VideoDetailResponse(VideoResponse):
    tracks: Optional[List[Any]] = []

class VideoFilter(BaseModel):
    camera_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20

class VideoUploadResponse(BaseModel):
    task_id: str
    video_id: uuid.UUID
    filename: str
    status: str
    message: str

class VideoStatusResponse(BaseModel):
    task_id: str
    video_id: Optional[uuid.UUID] = None
    filename: str
    status: str
    progress: float
    current_frame: int = 0
    total_frames: int = 0
    tracks_count: int = 0
    processing_fps: float = 0.0
    video_url: Optional[str] = None
    error: Optional[str] = None

VideoTaskStatusResponse = VideoStatusResponse
