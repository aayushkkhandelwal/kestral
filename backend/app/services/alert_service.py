import uuid
from typing import Sequence
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.user import User
from app.repositories.alert_repository import AlertRepository
from app.repositories.camera_repository import CameraRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.alert import AlertCreate, AlertFilter, AlertAcknowledge


class AlertService:
    def __init__(self, db: Session):
        self.db = db
        self.alert_repo = AlertRepository(db)
        self.camera_repo = CameraRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_alert(self, alert_in: AlertCreate, current_user: User | None = None) -> Alert:
        if alert_in.camera_id:
            camera = self.camera_repo.get_by_id(alert_in.camera_id)
            if not camera:
                raise NotFoundException("Camera", str(alert_in.camera_id))

        alert = self.alert_repo.create_alert(
            alert_type=alert_in.alert_type,
            severity=alert_in.severity,
            message=alert_in.message,
            camera_id=alert_in.camera_id,
            metadata=getattr(alert_in, "alert_metadata", getattr(alert_in, "metadata", None))
        )

        self.audit_repo.log_action(
            action="CREATE_ALERT",
            resource="Alert",
            user_id=current_user.id if current_user else None,
            metadata={
                "alert_id": str(alert.id),
                "alert_type": alert.alert_type,
                "severity": alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity),
                "camera_id": str(alert.camera_id) if alert.camera_id else None
            }
        )

        return alert

    def get_by_id(self, alert_id: uuid.UUID) -> Alert:
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise NotFoundException("Alert", str(alert_id))
        return alert

    def list_alerts(
        self,
        filters: AlertFilter,
        current_user: User | None = None
    ) -> tuple[Sequence[Alert], int]:
        return self.alert_repo.search(
            camera_id=filters.camera_id,
            severity=filters.severity,
            status=filters.status,
            alert_type=filters.alert_type,
            start_date=filters.start_date,
            end_date=filters.end_date,
            page=filters.page,
            page_size=filters.page_size
        )

    def acknowledge_alert(
        self,
        alert_id: uuid.UUID,
        ack_in: AlertAcknowledge,
        current_user: User
    ) -> Alert:
        alert = self.alert_repo.acknowledge_alert(
            alert_id=alert_id,
            user_id=current_user.id,
            note=ack_in.note
        )
        if not alert:
            raise NotFoundException("Alert", str(alert_id))

        self.audit_repo.log_action(
            action="ACKNOWLEDGE_ALERT",
            resource="Alert",
            user_id=current_user.id,
            metadata={
                "alert_id": str(alert_id),
                "note": ack_in.note
            }
        )

        return alert
