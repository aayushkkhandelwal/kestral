import os
import uuid
import json
import zipfile
import cv2
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.surveillance_event import SurveillanceEvent
from app.models.evidence_clip import EvidenceClip
from app.models.event_screenshot import EventScreenshot
from app.models.monitored_zone import MonitoredZone
from app.models.video import Video
from app.models.camera import Camera
from app.repositories.event_repository import EventRepository
from app.repositories.zone_repository import ZoneRepository
from app.repositories.audit_repository import AuditRepository
from services.event_detector import EventDetector
from services.clip_buffer_service import ClipBufferService
from app.core.exceptions import EntityNotFoundException, ValidationException


class EventService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
        self.zone_repo = ZoneRepository(db)
        self.audit_service = AuditRepository(db)
        self.clip_service = ClipBufferService()
        self.detector = EventDetector()

    def get_event(self, event_id: uuid.UUID) -> SurveillanceEvent:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            raise EntityNotFoundException("SurveillanceEvent", str(event_id))
        return event

    def search_events(
        self,
        camera_id: Optional[uuid.UUID] = None,
        video_id: Optional[uuid.UUID] = None,
        event_type: Optional[str] = None,
        track_id: Optional[uuid.UUID] = None,
        person_number: Optional[int] = None,
        zone_id: Optional[uuid.UUID] = None,
        confidence_min: Optional[float] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "desc",
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[SurveillanceEvent], int]:
        offset = (page - 1) * page_size
        return self.event_repo.search_events(
            camera_id=camera_id,
            video_id=video_id,
            event_type=event_type,
            track_id=track_id,
            person_number=person_number,
            zone_id=zone_id,
            confidence_min=confidence_min,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            offset=offset,
            limit=page_size
        )

    def capture_screenshot(
        self,
        event_id: Optional[uuid.UUID],
        video_timestamp_sec: float,
        user_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> EventScreenshot:
        """Captures frame screenshot at video_timestamp_sec, computes SHA-256 and persists."""
        event = None
        video = None
        camera_id = None
        video_id = None

        if event_id:
            event = self.get_event(event_id)
            video_id = event.video_id
            camera_id = event.camera_id
            if event.video:
                video = event.video

        # Output folder
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        frames_dir = os.path.join(backend_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        screenshot_id = uuid.uuid4()
        filename = f"screenshot_{screenshot_id}.jpg"
        abs_path = os.path.join(frames_dir, filename)
        rel_path = f"/frames/{filename}"

        dimensions = "1920x1080"
        frame_number = int(round(video_timestamp_sec * 25.0))

        # If base64 provided directly from client video canvas:
        if image_base64:
            import base64
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            img_bytes = base64.b64decode(image_base64)
            with open(abs_path, "wb") as f:
                f.write(img_bytes)
            img = cv2.imread(abs_path)
            if img is not None:
                dimensions = f"{img.shape[1]}x{img.shape[0]}"
        elif video and os.path.exists(os.path.join(backend_dir, video.file_path.lstrip("/"))):
            # Extract directly from source video file
            src_video = os.path.join(backend_dir, video.file_path.lstrip("/"))
            cap = cv2.VideoCapture(src_video)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_idx = int(round(video_timestamp_sec * fps))
            frame_number = frame_idx
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                cv2.imwrite(abs_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                dimensions = f"{frame.shape[1]}x{frame.shape[0]}"
            else:
                # Blank fallback frame
                blank = np.zeros((720, 1280, 3), dtype=np.uint8)
                cv2.imwrite(abs_path, blank)
        else:
            # Fallback canvas snapshot
            blank = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.imwrite(abs_path, blank)

        sha256 = self.clip_service.calculate_sha256(abs_path) if os.path.exists(abs_path) else None

        screenshot = self.event_repo.create_screenshot(
            event_id=event_id,
            image_path=rel_path,
            video_timestamp_sec=video_timestamp_sec,
            frame_number=frame_number,
            sha256=sha256,
            dimensions=dimensions,
            notes=notes,
            camera_id=camera_id,
            video_id=video_id,
            user_id=user_id
        )

        self.audit_service.log_action(
            action="CAPTURE_EVENT_SCREENSHOT",
            resource="EventScreenshot",
            user_id=user_id,
            metadata={"event_id": str(event_id) if event_id else None, "sha256": sha256, "screenshot_id": str(screenshot.screenshot_id)}
        )
        self.db.commit()
        return screenshot

    def ingest_transaction_webhook(
        self,
        atm_id: str,
        transaction_id: str,
        event_type: str = "transaction_start",
        timestamp_utc: Optional[datetime] = None,
        amount: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SurveillanceEvent:
        """Processes external transaction signal from ATM software/hardware webhook."""
        # Find matching camera for atm_id
        camera = self.db.query(Camera).filter(Camera.atm_id == atm_id).first()
        camera_id = camera.camera_id if camera else None

        meta = metadata or {}
        meta["transaction_id"] = transaction_id
        meta["atm_id"] = atm_id
        if amount is not None:
            meta["amount"] = amount

        event = self.event_repo.create_event(
            event_type=event_type,
            video_timestamp_sec=0.0,
            camera_id=camera_id,
            confidence=1.0,
            source="atm_webhook",
            event_metadata=meta,
            event_timestamp_utc=timestamp_utc or datetime.now(timezone.utc)
        )
        self.audit_service.log_action(
            action="INGEST_TRANSACTION_WEBHOOK",
            resource="SurveillanceEvent",
            metadata=meta
        )
        self.db.commit()
        return event

    def export_evidence_package(
        self,
        event_ids: List[uuid.UUID],
        user_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates sanitized ZIP bundle containing clips, screenshots, and SHA-256 manifest."""
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        exports_dir = os.path.join(backend_dir, "exports")
        os.makedirs(exports_dir, exist_ok=True)

        export_id = uuid.uuid4()
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_filename = f"kestral_evidence_export_{timestamp_str}_{str(export_id)[:8]}.zip"
        zip_abs_path = os.path.join(exports_dir, zip_filename)
        rel_url = f"/exports/{zip_filename}"

        events = [self.get_event(eid) for eid in event_ids]
        manifest_files = []

        with zipfile.ZipFile(zip_abs_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for ev in events:
                # 1. Add clip if exists
                if ev.clip and ev.clip.clip_path:
                    clip_file = os.path.join(backend_dir, ev.clip.clip_path.lstrip("/"))
                    if os.path.exists(clip_file):
                        arcname = f"clips/{os.path.basename(clip_file)}"
                        zipf.write(clip_file, arcname=arcname)
                        manifest_files.append({
                            "type": "evidence_clip",
                            "event_id": str(ev.event_id),
                            "event_type": ev.event_type,
                            "arcname": arcname,
                            "sha256": ev.clip.sha256,
                            "file_size": ev.clip.file_size_bytes
                        })

                # 2. Add screenshots if exist
                for shot in ev.screenshots:
                    shot_file = os.path.join(backend_dir, shot.image_path.lstrip("/"))
                    if os.path.exists(shot_file):
                        arcname = f"screenshots/{os.path.basename(shot_file)}"
                        zipf.write(shot_file, arcname=arcname)
                        manifest_files.append({
                            "type": "screenshot",
                            "event_id": str(ev.event_id),
                            "screenshot_id": str(shot.screenshot_id),
                            "arcname": arcname,
                            "sha256": shot.sha256
                        })

            # 3. Add Manifest JSON
            manifest_data = {
                "export_id": str(export_id),
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "exported_by_user_id": str(user_id) if user_id else None,
                "notes": notes,
                "events_count": len(events),
                "files": manifest_files,
                "forensic_integrity": "Cryptographic SHA-256 digests verify byte-level authenticity of each exported artifact."
            }
            zipf.writestr("manifest.json", json.dumps(manifest_data, indent=2))

        file_size = os.path.getsize(zip_abs_path) if os.path.exists(zip_abs_path) else 0
        zip_sha256 = self.clip_service.calculate_sha256(zip_abs_path) if file_size > 0 else ""

        self.audit_service.log_action(
            action="EXPORT_EVIDENCE_PACKAGE",
            resource="EvidenceExport",
            user_id=user_id,
            metadata={
                "export_id": str(export_id),
                "event_ids": [str(eid) for eid in event_ids],
                "sha256": zip_sha256,
                "file_size": file_size
            }
        )
        self.db.commit()

        return {
            "export_id": export_id,
            "export_filename": zip_filename,
            "download_url": rel_url,
            "file_size_bytes": file_size,
            "sha256": zip_sha256,
            "events_included_count": len(events),
            "created_at": datetime.now(timezone.utc)
        }
