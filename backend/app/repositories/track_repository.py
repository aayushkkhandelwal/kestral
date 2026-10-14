import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.person_track import PersonTrack
from app.repositories.base import BaseRepository

class TrackRepository(BaseRepository[PersonTrack]):
    def __init__(self, db: Session):
        super().__init__(PersonTrack, db)

    def get_by_video_and_person(self, video_id: uuid.UUID, person_number: int) -> Optional[PersonTrack]:
        stmt = select(PersonTrack).where(
            PersonTrack.video_id == video_id,
            PersonTrack.person_number == person_number
        )
        return self.db.scalars(stmt).first()

    def list_by_video(self, video_id: uuid.UUID) -> List[PersonTrack]:
        stmt = select(PersonTrack).where(PersonTrack.video_id == video_id).order_by(PersonTrack.person_number.asc())
        return list(self.db.scalars(stmt).all())
