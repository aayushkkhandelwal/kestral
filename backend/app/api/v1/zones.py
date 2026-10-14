import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user
from app.models.user import User
from app.schemas.zone import ZoneCreate, ZoneUpdate, ZoneResponse
from app.schemas.common import PaginatedResponse
from app.repositories.zone_repository import ZoneRepository

router = APIRouter(prefix="/zones", tags=["Monitored Zones"])


@router.get("", response_model=PaginatedResponse[ZoneResponse])
def list_zones(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    camera_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50
):
    repo = ZoneRepository(db)
    offset = (page - 1) * page_size
    items, total = repo.list_zones(camera_id=camera_id, is_active=is_active, offset=offset, limit=page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(
    zone_in: ZoneCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    repo = ZoneRepository(db)
    zone = repo.create_zone(
        name=zone_in.name,
        coordinates=zone_in.coordinates,
        zone_type=zone_in.zone_type,
        camera_id=zone_in.camera_id,
        is_active=zone_in.is_active
    )
    db.commit()
    return zone


@router.get("/{zone_id}", response_model=ZoneResponse)
def get_zone(
    zone_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    repo = ZoneRepository(db)
    zone = repo.get_by_id(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Monitored zone not found")
    return zone


@router.put("/{zone_id}", response_model=ZoneResponse)
def update_zone(
    zone_id: uuid.UUID,
    zone_update: ZoneUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    repo = ZoneRepository(db)
    zone = repo.get_by_id(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Monitored zone not found")

    if zone_update.name is not None:
        zone.name = zone_update.name
    if zone_update.zone_type is not None:
        zone.zone_type = zone_update.zone_type
    if zone_update.coordinates is not None:
        zone.coordinates = zone_update.coordinates
    if zone_update.is_active is not None:
        zone.is_active = zone_update.is_active

    db.commit()
    db.refresh(zone)
    return zone


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    zone_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    repo = ZoneRepository(db)
    zone = repo.get_by_id(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Monitored zone not found")
    db.delete(zone)
    db.commit()
    return None
