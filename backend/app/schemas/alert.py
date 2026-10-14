import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.alert import AlertSeverity

class AlertBase(BaseModel):
    camera_id: Optional[uuid.UUID] = None
    alert_type: str = Field(min_length=2, max_length=64)
    severity: str = "medium"
    message: str = Field(min_length=3)
    timestamp: Optional[datetime] = None
    alert_metadata: Optional[Dict[str, Any]] = None

class AlertCreate(AlertBase):
    pass

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: uuid.UUID
    id: Optional[uuid.UUID] = None
    camera_id: Optional[uuid.UUID] = None
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[uuid.UUID] = None
    is_acknowledged: bool = False
    alert_metadata: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context):
        if self.id is None:
            self.id = self.alert_id
        if self.acknowledged_at is not None:
            self.is_acknowledged = True

class AcknowledgeAlertRequest(BaseModel):
    note: Optional[str] = None
    message: Optional[str] = None

    def model_post_init(self, __context):
        if not self.note and self.message:
            self.note = self.message

AlertAcknowledge = AcknowledgeAlertRequest

class AlertFilter(BaseModel):
    camera_id: Optional[uuid.UUID] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    alert_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
