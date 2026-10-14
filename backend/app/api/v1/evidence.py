import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user, require_permission
from app.models.user import User
from app.schemas.evidence import EvidenceResponse, EvidenceSearchFilter, IntegrityVerificationResponse
from app.schemas.common import PaginatedResponse
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.get("", response_model=PaginatedResponse[EvidenceResponse])
def search_evidence(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    video_id: uuid.UUID | None = None,
    camera_id: uuid.UUID | None = None,
    track_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
    is_best: bool | None = None,
    min_quality: float | None = None,
    max_quality: float | None = None,
    quality_grade: str | None = None,
    person_number: int | None = None,
    page: int = 1,
    page_size: int = 50
):
    service = EvidenceService(db)
    filters = EvidenceSearchFilter(
        video_id=video_id,
        camera_id=camera_id,
        track_id=track_id,
        case_id=case_id,
        is_best=is_best,
        min_quality=min_quality,
        max_quality=max_quality,
        quality_grade=quality_grade,
        person_number=person_number,
        page=page,
        page_size=page_size
    )
    items, total = service.search_evidence(filters, current_user=current_user)
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=[EvidenceResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/best", response_model=PaginatedResponse[EvidenceResponse])
def get_best_evidence(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    video_id: uuid.UUID | None = None,
    camera_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 50
):
    service = EvidenceService(db)
    items, total = service.get_best_evidence_list(
        video_id=video_id,
        camera_id=camera_id,
        page=page,
        page_size=page_size
    )
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=[EvidenceResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(
    evidence_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = EvidenceService(db)
    return service.get_by_id(evidence_id)


@router.post("/{evidence_id}/verify", response_model=IntegrityVerificationResponse)
def verify_evidence_hash(
    evidence_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = EvidenceService(db)
    return service.verify_evidence_integrity(evidence_id, user=current_user)
