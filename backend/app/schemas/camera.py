import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.camera import CameraStatus

class CameraBase(BaseModel):
    camera_name: str = Field(min_length=2, max_length=128)
    name: Optional[str] = None
    atm_id: Optional[str] = Field(None, max_length=64)
    location: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    status: str = "online"

    def model_post_init(self, __context):
        if not self.camera_name and self.name:
            self.camera_name = self.name
        if not self.name and self.camera_name:
            self.name = self.camera_name

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    camera_name: Optional[str] = Field(None, min_length=2, max_length=128)
    name: Optional[str] = None
    atm_id: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None

class CameraResponse(CameraBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    camera_id: uuid.UUID
    id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    def model_post_init(self, __context):
        super().model_post_init(__context)
        if self.id is None:
            self.id = self.camera_id

class CameraFilter(BaseModel):
    status: Optional[str] = None
    location: Optional[str] = None
    atm_id: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 50
