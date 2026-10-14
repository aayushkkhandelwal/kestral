import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.time import utc_now


class QualityGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    POOR = "POOR"


class FaceEvidence(Base):
    __tablename__ = "face_evidence"

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("person_tracks.track_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    face_crop_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    full_frame_path: Mapped[str] = mapped_column(String(512), nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    quality_grade: Mapped[str] = mapped_column(String(8), nullable=False, default="C", index=True)
    sharpness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    brightness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    contrast: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    resolution: Mapped[str] = mapped_column(String(32), default="0x0", nullable=False)
    face_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    sha256_crop: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sha256_frame: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True
    )

    # Relationships
    track = relationship("PersonTrack", back_populates="evidence_records", foreign_keys=[track_id])
    cases = relationship("CaseEvidence", back_populates="evidence", cascade="all, delete-orphan")

    __table_args__ = (
        Index(
            "uq_track_best_evidence",
            "track_id",
            unique=True,
            postgresql_where=text("is_best = true"),
            sqlite_where=text("is_best = 1")
        ),
    )

    @property
    def id(self) -> uuid.UUID:
        return self.evidence_id

    @property
    def face_hash(self) -> str:
        return self.sha256_crop or ""

    @property
    def frame_hash(self) -> str:
        return self.sha256_frame or ""
