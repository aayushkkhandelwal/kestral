import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.time import utc_now


class EvidenceClip(Base):
    __tablename__ = "evidence_clips"

    clip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveillance_events.event_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    clip_path: Mapped[str] = mapped_column(String(512), nullable=False)
    clip_start_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    clip_end_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pre_event_duration: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    post_event_duration: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    export_status: Mapped[str] = mapped_column(String(32), default="available", nullable=False)  # available, exported, failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    event = relationship("SurveillanceEvent", back_populates="clip")
    video = relationship("Video")
