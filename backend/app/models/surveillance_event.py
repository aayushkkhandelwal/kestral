import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.time import utc_now


class EventType(str, Enum):
    PERSON_ENTRY = "person_entry"
    PERSON_EXIT = "person_exit"
    TRANSACTION_START = "transaction_start"
    LOITERING = "loitering"
    INFERRED_TRANSACTION = "inferred_transaction"


class EventStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"


class SurveillanceEvent(Base):
    __tablename__ = "surveillance_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    camera_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.camera_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    track_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("person_tracks.track_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitored_zones.zone_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    event_timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False
    )
    video_timestamp_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_frame: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    person_number: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    zone_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="vision_analytics", nullable=False)  # vision_analytics, atm_webhook, inferred_rule
    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    camera = relationship("Camera")
    video = relationship("Video")
    track = relationship("PersonTrack")
    zone = relationship("MonitoredZone", back_populates="events")
    clip = relationship("EvidenceClip", back_populates="event", uselist=False, cascade="all, delete-orphan")
    screenshots = relationship("EventScreenshot", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_events_type_timestamp", "event_type", "event_timestamp_utc"),
        Index("ix_events_video_time", "video_id", "video_timestamp_sec"),
    )
