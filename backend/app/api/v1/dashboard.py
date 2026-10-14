from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user, require_permission
from app.models.user import User
from app.schemas.dashboard import AdminStatsResponse, LegacyStatsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=AdminStatsResponse)
def get_metrics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = DashboardService(db)
    return service.get_admin_metrics()


@router.get("/stats", response_model=LegacyStatsResponse)
def get_legacy_stats(
    db: Annotated[Session, Depends(get_db)]
):
    service = DashboardService(db)
    return service.get_legacy_stats()
