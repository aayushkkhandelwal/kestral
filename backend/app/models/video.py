import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.time import utc_now


class VideoStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Also alias ProcessingStatus for backward compatibility
ProcessingStatus = VideoStatus


class Video(Base):
    __tablename__ = "videos"

    video_id: Mapped[uuid.UUID] = mapped_column(
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
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    resolution: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    camera = relationship("Camera", back_populates="videos")
    uploader = relationship("User", back_populates="videos")
    tracks = relationship("PersonTrack", back_populates="video", cascade="all, delete-orphan")

    @property
    def id(self) -> uuid.UUID:
        return self.video_id

    @property
    def storage_path(self) -> str:
        return self.file_path

    @property
    def file_size(self) -> int:
        return self.file_size_bytes

    @property
    def sha256_hash(self) -> str:
        return self.sha256 or ""

    @property
    def status(self) -> str:
        return self.processing_status

    @property
    def completed_at(self) -> datetime | None:
        return self.processed_at
