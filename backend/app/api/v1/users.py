import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_role, require_permission
from app.core.permissions import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.common import PaginatedResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
    db: Annotated[Session, Depends(get_db)]
):
    service = UserService(db)
    return service.create_user(user_in, current_user=current_user)


@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    current_user: Annotated[User, Depends(require_permission("users:read"))],
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 50
):
    service = UserService(db)
    items, total = service.list_users(skip=skip, limit=limit)
    page = (skip // limit) + 1 if limit > 0 else 1
    pages = (total + limit - 1) // limit if limit > 0 else 1
    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in items],
        total=total,
        page=page,
        page_size=limit,
        pages=pages
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_permission("users:read"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = UserService(db)
    return service.get_by_id(user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
    db: Annotated[Session, Depends(get_db)]
):
    service = UserService(db)
    return service.update_user(user_id, user_in, current_user=current_user)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
    db: Annotated[Session, Depends(get_db)]
):
    service = UserService(db)
    service.delete_user(user_id, current_user=current_user)
    return {"message": "User deleted successfully", "user_id": str(user_id)}
