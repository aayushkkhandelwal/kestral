import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.utils.time import utc_now


class CameraStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class Camera(Base):
    __tablename__ = "cameras"

    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    camera_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    atm_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="online", nullable=False)
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
    videos = relationship("Video", back_populates="camera")
    alerts = relationship("Alert", back_populates="camera")

    @property
    def id(self) -> uuid.UUID:
        return self.camera_id

    @property
    def name(self) -> str:
        return self.camera_name
