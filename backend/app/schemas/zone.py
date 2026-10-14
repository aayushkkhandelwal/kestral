import uuid
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class ZoneCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    zone_type: str = Field("polygon", pattern="^(polygon|tripwire)$")
    camera_id: Optional[uuid.UUID] = None
    coordinates: List[List[float]] = Field(..., min_length=3)
    is_active: bool = True


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    zone_type: Optional[str] = None
    coordinates: Optional[List[List[float]]] = None
    is_active: Optional[bool] = None


class ZoneResponse(BaseModel):
    zone_id: uuid.UUID
    camera_id: Optional[uuid.UUID] = None
    name: str
    zone_type: str
    coordinates: Any
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
