import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.monitored_zone import MonitoredZone
from app.repositories.base import BaseRepository


class ZoneRepository(BaseRepository[MonitoredZone]):
    def __init__(self, db: Session):
        super().__init__(MonitoredZone, db)

    def get_by_id(self, zone_id: uuid.UUID) -> Optional[MonitoredZone]:
        stmt = select(MonitoredZone).where(MonitoredZone.zone_id == zone_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_zones(
        self,
        camera_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[MonitoredZone], int]:
        stmt = select(MonitoredZone)
        count_stmt = select(func.count()).select_from(MonitoredZone)

        if camera_id is not None:
            stmt = stmt.where(MonitoredZone.camera_id == camera_id)
            count_stmt = count_stmt.where(MonitoredZone.camera_id == camera_id)

        if is_active is not None:
            stmt = stmt.where(MonitoredZone.is_active == is_active)
            count_stmt = count_stmt.where(MonitoredZone.is_active == is_active)

        total = self.db.execute(count_stmt).scalar() or 0
        items = list(self.db.execute(stmt.order_by(MonitoredZone.created_at.desc()).offset(offset).limit(limit)).scalars().all())
        return items, total

    def create_zone(
        self,
        name: str,
        coordinates: list,
        zone_type: str = "polygon",
        camera_id: Optional[uuid.UUID] = None,
        is_active: bool = True
    ) -> MonitoredZone:
        zone = MonitoredZone(
            name=name,
            coordinates=coordinates,
            zone_type=zone_type,
            camera_id=camera_id,
            is_active=is_active
        )
        self.db.add(zone)
        self.db.flush()
        return zone
