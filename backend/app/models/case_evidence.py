import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.time import utc_now


class CaseEvidence(Base):
    __tablename__ = "case_evidence"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigation_cases.case_id", ondelete="CASCADE"),
        primary_key=True
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("face_evidence.evidence_id", ondelete="RESTRICT"),
        primary_key=True
    )
    added_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    case = relationship("InvestigationCase", back_populates="case_evidence")
    evidence = relationship("FaceEvidence", back_populates="cases")
    added_by_user = relationship("User", foreign_keys=[added_by])

    @property
    def added_by_id(self) -> uuid.UUID | None:
        return self.added_by
