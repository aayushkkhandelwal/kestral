import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AuthenticationFailedException
from app.schemas.auth import TokenResponse, LoginRequest

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def login(self, request: LoginRequest, request_id: Optional[str] = None) -> TokenResponse:
        user = self.user_repo.get_by_email(request.email)
        if not user or not user.is_active:
            self.audit_repo.record_action(
                action="auth.login.failed",
                resource="user",
                request_id=request_id,
                details={"email": request.email, "reason": "User not found or inactive"}
            )
            self.db.commit()
            raise AuthenticationFailedException("Invalid email or password.")

        if not verify_password(request.password, user.password_hash):
            self.audit_repo.record_action(
                action="auth.login.failed",
                resource="user",
                user_id=user.id,
                request_id=request_id,
                details={"email": request.email, "reason": "Invalid password"}
            )
            self.db.commit()
            raise AuthenticationFailedException("Invalid email or password.")

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": role_str,
            "name": user.name,
            "type": "access"
        }
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        self.audit_repo.record_action(
            action="auth.login.success",
            resource="user",
            user_id=user.id,
            request_id=request_id,
            details={"email": user.email, "role": role_str}
        )
        self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=role_str,
            email=user.email,
            name=user.name
        )

    def logout(self, user, token: Optional[str] = None, request_id: Optional[str] = None):
        self.audit_repo.record_action(
            action="auth.logout",
            resource="user",
            user_id=user.id,
            request_id=request_id,
            details={"email": user.email}
        )
        self.db.commit()
        return {"message": "Logged out successfully"}

    authenticate = login

    def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh" and payload.get("token_type") != "refresh":
                raise AuthenticationFailedException("Invalid token type for refresh.")
            user_id = uuid.UUID(payload.get("sub"))
            user = self.user_repo.get_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationFailedException("User not found or inactive.")

            role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
            new_payload = {
                "sub": str(user.id),
                "email": user.email,
                "role": role_str,
                "name": user.name,
                "type": "access"
            }
            new_access = create_access_token(new_payload)
            new_refresh = create_refresh_token(new_payload)

            return TokenResponse(
                access_token=new_access,
                refresh_token=new_refresh,
                role=role_str,
                email=user.email,
                name=user.name
            )
        except Exception as e:
            raise AuthenticationFailedException(f"Token refresh failed: {str(e)}")
