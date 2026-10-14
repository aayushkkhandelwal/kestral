from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        return self.db.scalars(stmt).first()

    def list_users(self, offset: int = 0, limit: int = 50, active_only: bool = False) -> List[User]:
        stmt = select(User)
        if active_only:
            stmt = stmt.where(User.is_active == True)
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())
