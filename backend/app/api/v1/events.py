import uuid
from datetime import datetime
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user
from app.models.user import User
from app.schemas.event import (
    SurveillanceEventResponse,
    ClipResponse,
    ScreenshotCreate,
    ScreenshotResponse,
    TransactionWebhookPayload,
    EvidenceExportRequest,
    EvidenceExportResponse
)
from app.schemas.common import PaginatedResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Surveillance Events & Evidence Review"])


@router.get("", response_model=PaginatedResponse[SurveillanceEventResponse])
def list_events(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    camera_id: Optional[uuid.UUID] = None,
    video_id: Optional[uuid.UUID] = None,
    event_type: Optional[str] = None,
    track_id: Optional[uuid.UUID] = None,
    person_number: Optional[int] = None,
    zone_id: Optional[uuid.UUID] = None,
    confidence_min: Optional[float] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = Query("desc", pattern="^(desc|asc)$"),
    page: int = 1,
    page_size: int = 50
):
    service = EventService(db)
    items, total = service.search_events(
        camera_id=camera_id,
        video_id=video_id,
        event_type=event_type,
        track_id=track_id,
        person_number=person_number,
        zone_id=zone_id,
        confidence_min=confidence_min,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{event_id}", response_model=SurveillanceEventResponse)
def get_event(
    event_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = EventService(db)
    return service.get_event(event_id)


@router.get("/{event_id}/clip", response_model=ClipResponse)
def get_event_clip(
    event_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = EventService(db)
    event = service.get_event(event_id)
    if not event.clip:
        raise HTTPException(status_code=404, detail="Evidence clip not yet generated or available for this event")
    return event.clip


@router.get("/{event_id}/screenshots", response_model=List[ScreenshotResponse])
def get_event_screenshots(
    event_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = EventService(db)
    event = service.get_event(event_id)
    return event.screenshots or []


@router.post("/{event_id}/screenshots", response_model=ScreenshotResponse, status_code=status.HTTP_201_CREATED)
def capture_event_screenshot(
    event_id: uuid.UUID,
    payload: ScreenshotCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = EventService(db)
    user_id = current_user.id if current_user else None
    return service.capture_screenshot(
        event_id=event_id,
        video_timestamp_sec=payload.video_timestamp_sec,
        user_id=user_id,
        notes=payload.notes,
        image_base64=payload.image_base64
    )


@router.post("/transaction-webhook", response_model=SurveillanceEventResponse, status_code=status.HTTP_201_CREATED)
def receive_transaction_webhook(
    payload: TransactionWebhookPayload,
    db: Annotated[Session, Depends(get_db)]
):
    service = EventService(db)
    return service.ingest_transaction_webhook(
        atm_id=payload.atm_id,
        transaction_id=payload.transaction_id,
        event_type=payload.event_type,
        timestamp_utc=payload.timestamp_utc,
        amount=payload.amount,
        metadata=payload.metadata
    )


@router.post("/export", response_model=EvidenceExportResponse)
def export_evidence(
    payload: EvidenceExportRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = EventService(db)
    user_id = current_user.id if current_user else None
    res = service.export_evidence_package(
        event_ids=payload.event_ids,
        user_id=user_id,
        notes=payload.export_notes
    )
    return res
