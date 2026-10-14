import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.time import utc_now


class EventScreenshot(Base):
    __tablename__ = "event_screenshots"

    screenshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("surveillance_events.event_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    camera_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.camera_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    captured_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    video_timestamp_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    dimensions: Mapped[str] = mapped_column(String(32), default="1920x1080", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    captured_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    event = relationship("SurveillanceEvent", back_populates="screenshots")
    video = relationship("Video")
    camera = relationship("Camera")
    user = relationship("User")
