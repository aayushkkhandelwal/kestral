import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.investigation_case import CaseStatus
from app.schemas.evidence import EvidenceResponse

class CaseBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: Optional[str] = None
    status: str = "open"

class CaseCreate(CaseBase):
    assigned_to: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None

    def model_post_init(self, __context):
        if not self.assigned_to and self.assigned_to_id:
            self.assigned_to = self.assigned_to_id

class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None

    def model_post_init(self, __context):
        if not self.assigned_to and self.assigned_to_id:
            self.assigned_to = self.assigned_to_id

class CaseResponse(CaseBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    case_id: uuid.UUID
    id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0

    def model_post_init(self, __context):
        if self.id is None:
            self.id = self.case_id
        if self.assigned_to_id is None:
            self.assigned_to_id = self.assigned_to
        if self.created_by_id is None:
            self.created_by_id = self.created_by

class CaseDetailResponse(CaseResponse):
    evidence: List[EvidenceResponse] = []

class AssignEvidenceRequest(BaseModel):
    evidence_ids: List[uuid.UUID]

CaseAssignEvidenceRequest = AssignEvidenceRequest

class CaseFilter(BaseModel):
    status: Optional[str] = None
    assigned_to_id: Optional[uuid.UUID] = None
    created_by_id: Optional[uuid.UUID] = None
    search: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 20

class CaseExportResponse(BaseModel):
    case_id: uuid.UUID
    export_filename: str
    download_url: str
    message: str
