from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserProfileResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Annotated[Session, Depends(get_db)]
):
    service = AuthService(db)
    return service.authenticate(login_data)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    service = AuthService(db)
    return service.logout(current_user)


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user
