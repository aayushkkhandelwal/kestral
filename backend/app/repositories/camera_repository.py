import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.camera import Camera, CameraStatus
from app.repositories.base import BaseRepository

class CameraRepository(BaseRepository[Camera]):
    def __init__(self, db: Session):
        super().__init__(Camera, db)

    def search_cameras(
        self,
        query: Optional[str] = None,
        status: Optional[CameraStatus] = None,
        atm_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[Camera], int]:
        stmt = select(Camera)
        count_stmt = select(func.count()).select_from(Camera)

        if query:
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(Camera.camera_name.ilike(pattern) | Camera.location.ilike(pattern))
            count_stmt = count_stmt.where(Camera.camera_name.ilike(pattern) | Camera.location.ilike(pattern))

        if status:
            stmt = stmt.where(Camera.status == status)
            count_stmt = count_stmt.where(Camera.status == status)

        if atm_id:
            stmt = stmt.where(Camera.atm_id == atm_id.strip())
            count_stmt = count_stmt.where(Camera.atm_id == atm_id.strip())

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.order_by(Camera.created_at.desc()).offset(offset).limit(limit)).all())
        return items, total
