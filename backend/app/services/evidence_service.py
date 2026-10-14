import uuid
from typing import Sequence
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.face_evidence import FaceEvidence
from app.models.user import User
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.evidence import EvidenceFilter, EvidenceSearchFilter


class EvidenceService:
    def __init__(self, db: Session):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.audit_repo = AuditRepository(db)

    def get_by_id(self, evidence_id: uuid.UUID) -> FaceEvidence:
        evidence = self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise NotFoundException("FaceEvidence", str(evidence_id))
        return evidence

    def search_evidence(
        self,
        filters: EvidenceSearchFilter,
        current_user: User | None = None
    ) -> tuple[Sequence[FaceEvidence], int]:
        items, total = self.evidence_repo.search(
            video_id=filters.video_id,
            camera_id=filters.camera_id,
            track_id=filters.track_id,
            case_id=filters.case_id,
            is_best=filters.is_best,
            min_quality=filters.min_quality,
            max_quality=filters.max_quality,
            quality_grade=filters.quality_grade,
            person_number=filters.person_number,
            start_date=filters.start_date,
            end_date=filters.end_date,
            page=filters.page,
            page_size=filters.page_size
        )
        return items, total

    def get_best_evidence_list(
        self,
        video_id: uuid.UUID | None = None,
        camera_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[Sequence[FaceEvidence], int]:
        filters = EvidenceSearchFilter(
            video_id=video_id,
            camera_id=camera_id,
            is_best=True,
            page=page,
            page_size=page_size
        )
        return self.search_evidence(filters)

    def verify_evidence_integrity(
        self,
        evidence_id: uuid.UUID,
        user: User | None = None
    ) -> dict:
        evidence = self.get_by_id(evidence_id)
        import os
        from app.utils.hashing import calculate_sha256
        from app.core.config import get_settings

        settings = get_settings()
        full_face_path = settings.get_storage_path(evidence.face_crop_path)
        full_frame_path = settings.get_storage_path(evidence.full_frame_path)

        face_exists = os.path.exists(full_face_path)
        frame_exists = os.path.exists(full_frame_path)

        face_match = False
        frame_match = False

        if face_exists:
            current_face_hash = calculate_sha256(full_face_path)
            face_match = (current_face_hash == evidence.face_hash)
        else:
            current_face_hash = None

        if frame_exists:
            current_frame_hash = calculate_sha256(full_frame_path)
            frame_match = (current_frame_hash == evidence.frame_hash)
        else:
            current_frame_hash = None

        is_intact = face_exists and frame_exists and face_match and frame_match

        self.audit_repo.log_action(
            action="VERIFY_INTEGRITY",
            resource="FaceEvidence",
            user_id=user.id if user else None,
            metadata={
                "evidence_id": str(evidence.id),
                "is_intact": is_intact,
                "face_match": face_match,
                "frame_match": frame_match
            }
        )

        return {
            "evidence_id": evidence.id,
            "face_crop_exists": face_exists,
            "full_frame_exists": frame_exists,
            "face_hash_recorded": evidence.face_hash,
            "face_hash_current": current_face_hash,
            "face_hash_matches": face_match,
            "frame_hash_recorded": evidence.frame_hash,
            "frame_hash_current": current_frame_hash,
            "frame_hash_matches": frame_match,
            "is_valid": is_intact
        }
