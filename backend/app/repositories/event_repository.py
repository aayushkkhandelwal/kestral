import uuid
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, desc, asc
from sqlalchemy.orm import Session, joinedload

from app.models.surveillance_event import SurveillanceEvent
from app.models.evidence_clip import EvidenceClip
from app.models.event_screenshot import EventScreenshot
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[SurveillanceEvent]):
    def __init__(self, db: Session):
        super().__init__(SurveillanceEvent, db)

    def get_by_id(self, event_id: uuid.UUID) -> Optional[SurveillanceEvent]:
        stmt = (
            select(SurveillanceEvent)
            .options(
                joinedload(SurveillanceEvent.clip),
                joinedload(SurveillanceEvent.screenshots),
                joinedload(SurveillanceEvent.camera),
                joinedload(SurveillanceEvent.zone)
            )
            .where(SurveillanceEvent.event_id == event_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def search_events(
        self,
        camera_id: Optional[uuid.UUID] = None,
        video_id: Optional[uuid.UUID] = None,
        event_type: Optional[str] = None,
        track_id: Optional[uuid.UUID] = None,
        person_number: Optional[int] = None,
        zone_id: Optional[uuid.UUID] = None,
        confidence_min: Optional[float] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "desc",
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[SurveillanceEvent], int]:
        stmt = (
            select(SurveillanceEvent)
            .options(
                joinedload(SurveillanceEvent.clip),
                joinedload(SurveillanceEvent.screenshots)
            )
        )
        count_stmt = select(func.count()).select_from(SurveillanceEvent)

        if camera_id is not None:
            stmt = stmt.where(SurveillanceEvent.camera_id == camera_id)
            count_stmt = count_stmt.where(SurveillanceEvent.camera_id == camera_id)

        if video_id is not None:
            stmt = stmt.where(SurveillanceEvent.video_id == video_id)
            count_stmt = count_stmt.where(SurveillanceEvent.video_id == video_id)

        if event_type:
            stmt = stmt.where(SurveillanceEvent.event_type == event_type)
            count_stmt = count_stmt.where(SurveillanceEvent.event_type == event_type)

        if track_id is not None:
            stmt = stmt.where(SurveillanceEvent.track_id == track_id)
            count_stmt = count_stmt.where(SurveillanceEvent.track_id == track_id)

        if person_number is not None:
            stmt = stmt.where(SurveillanceEvent.person_number == person_number)
            count_stmt = count_stmt.where(SurveillanceEvent.person_number == person_number)

        if zone_id is not None:
            stmt = stmt.where(SurveillanceEvent.zone_id == zone_id)
            count_stmt = count_stmt.where(SurveillanceEvent.zone_id == zone_id)

        if confidence_min is not None:
            stmt = stmt.where(SurveillanceEvent.confidence >= confidence_min)
            count_stmt = count_stmt.where(SurveillanceEvent.confidence >= confidence_min)

        if date_from is not None:
            stmt = stmt.where(SurveillanceEvent.event_timestamp_utc >= date_from)
            count_stmt = count_stmt.where(SurveillanceEvent.event_timestamp_utc >= date_from)

        if date_to is not None:
            stmt = stmt.where(SurveillanceEvent.event_timestamp_utc <= date_to)
            count_stmt = count_stmt.where(SurveillanceEvent.event_timestamp_utc <= date_to)

        total = self.db.execute(count_stmt).scalar() or 0

        order_col = desc(SurveillanceEvent.event_timestamp_utc) if sort_by == "desc" else asc(SurveillanceEvent.event_timestamp_utc)
        items = list(self.db.execute(stmt.order_by(order_col).offset(offset).limit(limit)).unique().scalars().all())
        return items, total

    def create_event(
        self,
        event_type: str,
        video_timestamp_sec: float,
        camera_id: Optional[uuid.UUID] = None,
        video_id: Optional[uuid.UUID] = None,
        track_id: Optional[uuid.UUID] = None,
        person_number: Optional[int] = None,
        zone_id: Optional[uuid.UUID] = None,
        zone_name: Optional[str] = None,
        source_frame: int = 0,
        confidence: float = 1.0,
        source: str = "vision_analytics",
        event_metadata: Optional[Dict[str, Any]] = None,
        event_timestamp_utc: Optional[datetime] = None
    ) -> SurveillanceEvent:
        event = SurveillanceEvent(
            event_type=event_type,
            video_timestamp_sec=video_timestamp_sec,
            source_frame=source_frame,
            camera_id=camera_id,
            video_id=video_id,
            track_id=track_id,
            person_number=person_number,
            zone_id=zone_id,
            zone_name=zone_name,
            confidence=confidence,
            source=source,
            event_metadata=event_metadata or {},
            processing_status="completed"
        )
        if event_timestamp_utc:
            event.event_timestamp_utc = event_timestamp_utc
        self.db.add(event)
        self.db.flush()
        return event

    def create_clip(
        self,
        event_id: uuid.UUID,
        clip_path: str,
        clip_start_sec: float,
        clip_end_sec: float,
        pre_event_duration: float,
        post_event_duration: float,
        sha256: Optional[str] = None,
        file_size_bytes: int = 0,
        video_id: Optional[uuid.UUID] = None
    ) -> EvidenceClip:
        clip = EvidenceClip(
            event_id=event_id,
            video_id=video_id,
            clip_path=clip_path,
            clip_start_sec=clip_start_sec,
            clip_end_sec=clip_end_sec,
            pre_event_duration=pre_event_duration,
            post_event_duration=post_event_duration,
            sha256=sha256,
            file_size_bytes=file_size_bytes,
            export_status="available"
        )
        self.db.add(clip)
        self.db.flush()
        return clip

    def create_screenshot(
        self,
        event_id: Optional[uuid.UUID],
        image_path: str,
        video_timestamp_sec: float,
        frame_number: int,
        sha256: Optional[str] = None,
        dimensions: str = "1920x1080",
        notes: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        video_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> EventScreenshot:
        shot = EventScreenshot(
            event_id=event_id,
            image_path=image_path,
            video_timestamp_sec=video_timestamp_sec,
            frame_number=frame_number,
            sha256=sha256,
            dimensions=dimensions,
            notes=notes,
            camera_id=camera_id,
            video_id=video_id,
            captured_by_user_id=user_id
        )
        self.db.add(shot)
        self.db.flush()
        return shot
