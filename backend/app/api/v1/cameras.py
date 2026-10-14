import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_optional_current_user, require_permission
from app.models.user import User
from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse, CameraFilter
from app.schemas.common import PaginatedResponse
from app.services.camera_service import CameraService

router = APIRouter(prefix="/camera", tags=["Cameras"])


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(
    camera_in: CameraCreate,
    current_user: Annotated[User, Depends(require_permission("cameras:write"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = CameraService(db)
    return service.create_camera(camera_in, current_user=current_user)


@router.get("", response_model=PaginatedResponse[CameraResponse])
def list_cameras(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    status: str | None = None,
    location: str | None = None,
    atm_id: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50
):
    service = CameraService(db)
    filters = CameraFilter(
        status=status,
        location=location,
        atm_id=atm_id,
        search=search,
        page=page,
        page_size=page_size
    )
    items, total = service.list_cameras(filters, current_user=current_user)
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=[CameraResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(
    camera_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = CameraService(db)
    return service.get_by_id(camera_id)


@router.put("/{camera_id}", response_model=CameraResponse)
def update_camera(
    camera_id: uuid.UUID,
    camera_in: CameraUpdate,
    current_user: Annotated[User, Depends(require_permission("cameras:write"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = CameraService(db)
    return service.update_camera(camera_id, camera_in, current_user=current_user)


@router.delete("/{camera_id}", status_code=status.HTTP_200_OK)
def delete_camera(
    camera_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_permission("cameras:delete"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = CameraService(db)
    service.delete_camera(camera_id, current_user=current_user)
    return {"message": "Camera deleted successfully", "camera_id": str(camera_id)}
