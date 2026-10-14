import uuid
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository

class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def record_action(
        self,
        action: str,
        resource: str,
        user_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Appends an immutable audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            request_id=request_id,
            details=details or {}
        )
        self.db.add(log)
        self.db.flush()
        return log

    def log_action(
        self,
        action: str,
        resource: str,
        user_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        return self.record_action(
            action=action,
            resource=resource,
            user_id=user_id,
            request_id=request_id,
            details=metadata
        )

    def list_logs(
        self,
        user_id: Optional[uuid.UUID] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        stmt = select(AuditLog)
        count_stmt = select(func.count()).select_from(AuditLog)

        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
            count_stmt = count_stmt.where(AuditLog.user_id == user_id)

        if resource:
            stmt = stmt.where(AuditLog.resource == resource)
            count_stmt = count_stmt.where(AuditLog.resource == resource)

        if action:
            stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
            count_stmt = count_stmt.where(AuditLog.action.ilike(f"%{action}%"))

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)).all())
        return items, total
