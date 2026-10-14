from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from app.schemas.video import VideoResponse, VideoUploadResponse, VideoStatusResponse
from app.schemas.person_track import PersonTrackResponse, PersonTrackDetailResponse
from app.schemas.evidence import EvidenceResponse, EvidenceExportRequest
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseDetailResponse, AssignEvidenceRequest
from app.schemas.alert import AlertCreate, AlertResponse, AcknowledgeAlertRequest
from app.schemas.dashboard import AdminStatsResponse, LegacyStatsResponse

__all__ = [
    "PaginatedResponse",
    "MessageResponse",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "VideoResponse",
    "VideoUploadResponse",
    "VideoStatusResponse",
    "PersonTrackResponse",
    "PersonTrackDetailResponse",
    "EvidenceResponse",
    "EvidenceExportRequest",
    "CaseCreate",
    "CaseUpdate",
    "CaseResponse",
    "CaseDetailResponse",
    "AssignEvidenceRequest",
    "AlertCreate",
    "AlertResponse",
    "AcknowledgeAlertRequest",
    "AdminStatsResponse",
    "LegacyStatsResponse",
]
