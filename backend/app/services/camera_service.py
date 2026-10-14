import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.camera import Camera, CameraStatus
from app.models.user import User
from app.repositories.camera_repository import CameraRepository
from app.repositories.audit_repository import AuditRepository
from app.core.exceptions import EntityNotFoundException
from app.schemas.camera import CameraCreate, CameraUpdate, CameraFilter

class CameraService:
    def __init__(self, db: Session):
        self.db = db
        self.camera_repo = CameraRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_camera(
        self,
        req: CameraCreate,
        current_user: Optional[User] = None,
        creator: Optional[User] = None,
        request_id: Optional[str] = None
    ) -> Camera:
        acting_user = current_user or creator
        name_val = req.camera_name or req.name or "Unnamed Camera"
        status_val = req.status.value if hasattr(req.status, "value") else str(req.status)
        camera = Camera(
            camera_name=name_val.strip(),
            atm_id=req.atm_id.strip() if req.atm_id else None,
            location=req.location.strip() if req.location else None,
            ip_address=req.ip_address.strip() if req.ip_address else None,
            status=status_val
        )
        self.camera_repo.add(camera)
        self.audit_repo.record_action(
            action="camera.create",
            resource="camera",
            user_id=acting_user.id if acting_user else None,
            request_id=request_id,
            details={"camera_id": str(camera.camera_id), "name": camera.camera_name}
        )
        self.db.commit()
        self.db.refresh(camera)
        return camera

    def get_camera(self, camera_id: uuid.UUID) -> Camera:
        camera = self.camera_repo.get_by_id(camera_id)
        if not camera:
            raise EntityNotFoundException("Camera", str(camera_id))
        return camera

    get_by_id = get_camera

    def search_cameras(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        atm_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[Camera], int]:
        return self.camera_repo.search_cameras(
            query=query,
            status=status,
            atm_id=atm_id,
            offset=offset,
            limit=limit
        )

    def list_cameras(
        self,
        filters: CameraFilter,
        current_user: Optional[User] = None
    ) -> Tuple[List[Camera], int]:
        offset = (filters.page - 1) * filters.page_size
        return self.search_cameras(
            query=filters.search,
            status=filters.status,
            atm_id=filters.atm_id,
            offset=offset,
            limit=filters.page_size
        )

    def update_camera(
        self,
        camera_id: uuid.UUID,
        req: CameraUpdate,
        current_user: Optional[User] = None,
        updater: Optional[User] = None,
        request_id: Optional[str] = None
    ) -> Camera:
        acting_user = current_user or updater
        camera = self.get_camera(camera_id)
        name_val = req.camera_name or req.name
        if name_val is not None:
            camera.camera_name = name_val.strip()
        if req.atm_id is not None:
            camera.atm_id = req.atm_id.strip() if req.atm_id else None
        if req.location is not None:
            camera.location = req.location.strip() if req.location else None
        if req.ip_address is not None:
            camera.ip_address = req.ip_address.strip() if req.ip_address else None
        if req.status is not None:
            camera.status = req.status.value if hasattr(req.status, "value") else str(req.status)

        self.camera_repo.add(camera)
        self.audit_repo.record_action(
            action="camera.update",
            resource="camera",
            user_id=acting_user.id if acting_user else None,
            request_id=request_id,
            details={"camera_id": str(camera_id)}
        )
        self.db.commit()
        self.db.refresh(camera)
        return camera

    def delete_camera(
        self,
        camera_id: uuid.UUID,
        current_user: Optional[User] = None
    ) -> bool:
        camera = self.get_camera(camera_id)
        self.camera_repo.delete(camera)
        self.audit_repo.record_action(
            action="camera.delete",
            resource="camera",
            user_id=current_user.id if current_user else None,
            details={"camera_id": str(camera_id), "name": camera.camera_name}
        )
        self.db.commit()
        return True
