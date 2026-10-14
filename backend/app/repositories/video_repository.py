import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.video import Video, ProcessingStatus
from app.repositories.base import BaseRepository

class VideoRepository(BaseRepository[Video]):
    def __init__(self, db: Session):
        super().__init__(Video, db)

    def search_videos(
        self,
        camera_id: Optional[uuid.UUID] = None,
        status: Optional[ProcessingStatus] = None,
        filename_query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[Video], int]:
        stmt = select(Video)
        count_stmt = select(func.count()).select_from(Video)

        if camera_id:
            stmt = stmt.where(Video.camera_id == camera_id)
            count_stmt = count_stmt.where(Video.camera_id == camera_id)

        if status:
            stmt = stmt.where(Video.processing_status == status)
            count_stmt = count_stmt.where(Video.processing_status == status)

        if filename_query:
            pattern = f"%{filename_query.strip()}%"
            stmt = stmt.where(Video.filename.ilike(pattern))
            count_stmt = count_stmt.where(Video.filename.ilike(pattern))

        if date_from:
            stmt = stmt.where(Video.created_at >= date_from)
            count_stmt = count_stmt.where(Video.created_at >= date_from)

        if date_to:
            stmt = stmt.where(Video.created_at <= date_to)
            count_stmt = count_stmt.where(Video.created_at <= date_to)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.order_by(Video.created_at.desc()).offset(offset).limit(limit)).all())
        return items, total
