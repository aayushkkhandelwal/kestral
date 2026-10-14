import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.core.security import hash_password
from app.core.permissions import UserRole, can_assign_role
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    PermissionDeniedException
)
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_user(
        self,
        req: UserCreate,
        current_user: Optional[User] = None,
        creator: Optional[User] = None,
        request_id: Optional[str] = None
    ) -> User:
        acting_user = current_user or creator

        # Check duplicate email
        existing = self.user_repo.get_by_email(req.email)
        if existing:
            raise DuplicateEntityException("User", "email", req.email)

        # Enforce privilege escalation check
        if acting_user and not can_assign_role(acting_user.role, req.role):
            raise PermissionDeniedException(f"Role '{acting_user.role}' cannot create users with role '{req.role}'.")

        role_str = req.role.value if hasattr(req.role, "value") else str(req.role)

        new_user = User(
            name=req.name.strip(),
            email=req.email.lower().strip(),
            password_hash=hash_password(req.password),
            role=role_str,
            is_active=req.is_active
        )
        self.user_repo.add(new_user)

        self.audit_repo.record_action(
            action="user.create",
            resource="user",
            user_id=acting_user.id if acting_user else None,
            request_id=request_id,
            details={"created_user_id": str(new_user.id), "email": new_user.email, "role": role_str}
        )
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", str(user_id))
        return user

    get_by_id = get_user_by_id

    def list_users(self, skip: int = 0, limit: int = 50, offset: Optional[int] = None) -> Tuple[List[User], int]:
        off = offset if offset is not None else skip
        return self.user_repo.list_users(offset=off, limit=limit)

    def update_user(
        self,
        user_id: uuid.UUID,
        req: UserUpdate,
        current_user: Optional[User] = None,
        updater: Optional[User] = None,
        request_id: Optional[str] = None
    ) -> User:
        acting_user = current_user or updater
        user = self.get_user_by_id(user_id)

        if req.name is not None:
            user.name = req.name.strip()
        if req.role is not None:
            if acting_user and not can_assign_role(acting_user.role, req.role):
                raise PermissionDeniedException("Only Admins can change user roles.")
            role_str = req.role.value if hasattr(req.role, "value") else str(req.role)
            user.role = role_str
        if req.is_active is not None:
            user.is_active = req.is_active
        if req.password is not None:
            user.password_hash = hash_password(req.password)

        self.user_repo.add(user)
        self.audit_repo.record_action(
            action="user.update",
            resource="user",
            user_id=acting_user.id if acting_user else None,
            request_id=request_id,
            details={"updated_user_id": str(user_id)}
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: uuid.UUID, current_user: Optional[User] = None) -> bool:
        user = self.get_user_by_id(user_id)
        self.user_repo.delete(user)
        self.audit_repo.record_action(
            action="user.delete",
            resource="user",
            user_id=current_user.id if current_user else None,
            details={"deleted_user_id": str(user_id)}
        )
        self.db.commit()
        return True
