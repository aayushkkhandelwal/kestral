import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_optional_current_user, require_permission
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertResponse, AlertFilter, AlertAcknowledge
from app.schemas.common import PaginatedResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_in: AlertCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = AlertService(db)
    return service.create_alert(alert_in, current_user=current_user)


@router.get("", response_model=PaginatedResponse[AlertResponse])
def list_alerts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    camera_id: uuid.UUID | None = None,
    severity: str | None = None,
    status: str | None = None,
    alert_type: str | None = None,
    page: int = 1,
    page_size: int = 50
):
    service = AlertService(db)
    filters = AlertFilter(
        camera_id=camera_id,
        severity=severity,
        status=status,
        alert_type=alert_type,
        page=page,
        page_size=page_size
    )
    items, total = service.list_alerts(filters, current_user=current_user)
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=[AlertResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = AlertService(db)
    return service.get_by_id(alert_id)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: uuid.UUID,
    ack_in: AlertAcknowledge,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None
):
    service = AlertService(db)
    return service.acknowledge_alert(alert_id, ack_in, current_user=current_user)
