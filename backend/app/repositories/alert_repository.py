import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.alert import Alert, AlertSeverity
from app.repositories.base import BaseRepository

class AlertRepository(BaseRepository[Alert]):
    def __init__(self, db: Session):
        super().__init__(Alert, db)

    def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        camera_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None
    ) -> Alert:
        sev_str = severity.value if hasattr(severity, "value") else str(severity)
        alert = Alert(
            alert_type=alert_type,
            severity=sev_str,
            message=message,
            camera_id=camera_id
        )
        self.db.add(alert)
        self.db.flush()
        return alert

    def acknowledge_alert(
        self,
        alert_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        note: Optional[str] = None
    ) -> Optional[Alert]:
        alert = self.get_by_id(alert_id)
        if not alert:
            return None
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = user_id
        self.db.add(alert)
        self.db.flush()
        return alert

    def search_alerts(
        self,
        camera_id: Optional[uuid.UUID] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        is_acknowledged: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[Alert], int]:
        stmt = select(Alert)
        count_stmt = select(func.count()).select_from(Alert)

        if camera_id:
            stmt = stmt.where(Alert.camera_id == camera_id)
            count_stmt = count_stmt.where(Alert.camera_id == camera_id)

        if severity:
            sev_str = severity.value if hasattr(severity, "value") else str(severity)
            stmt = stmt.where(Alert.severity == sev_str)
            count_stmt = count_stmt.where(Alert.severity == sev_str)

        if alert_type:
            stmt = stmt.where(Alert.alert_type == alert_type.strip())
            count_stmt = count_stmt.where(Alert.alert_type == alert_type.strip())

        if is_acknowledged is True:
            stmt = stmt.where(Alert.acknowledged_at.isnot(None))
            count_stmt = count_stmt.where(Alert.acknowledged_at.isnot(None))
        elif is_acknowledged is False:
            stmt = stmt.where(Alert.acknowledged_at.is_(None))
            count_stmt = count_stmt.where(Alert.acknowledged_at.is_(None))

        if date_from:
            stmt = stmt.where(Alert.timestamp >= date_from)
            count_stmt = count_stmt.where(Alert.timestamp >= date_from)

        if date_to:
            stmt = stmt.where(Alert.timestamp <= date_to)
            count_stmt = count_stmt.where(Alert.timestamp <= date_to)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.order_by(Alert.timestamp.desc()).offset(offset).limit(limit)).all())
        return items, total

    def search(
        self,
        camera_id: Optional[uuid.UUID] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        alert_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Alert], int]:
        offset = (page - 1) * page_size
        is_ack = None
        if status:
            if status.lower() == "acknowledged":
                is_ack = True
            elif status.lower() == "active":
                is_ack = False
        return self.search_alerts(
            camera_id=camera_id,
            severity=severity,
            alert_type=alert_type,
            is_acknowledged=is_ack,
            date_from=start_date,
            date_to=end_date,
            offset=offset,
            limit=page_size
        )
