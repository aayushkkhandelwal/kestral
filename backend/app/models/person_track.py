import uuid
from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.time import utc_now


class PersonTrack(Base):
    __tablename__ = "person_tracks"

    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.video_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    person_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_frame: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_frame: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_frames: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    best_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Relationships
    video = relationship("Video", back_populates="tracks")
    evidence_records = relationship(
        "FaceEvidence",
        back_populates="track",
        cascade="all, delete-orphan",
        foreign_keys="FaceEvidence.track_id"
    )

    __table_args__ = (
        UniqueConstraint("video_id", "person_number", name="uq_video_person_number"),
    )

    @property
    def id(self) -> uuid.UUID:
        return self.track_id
