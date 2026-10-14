import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from app.models.face_evidence import FaceEvidence, QualityGrade
from app.models.person_track import PersonTrack
from app.models.case_evidence import CaseEvidence
from app.repositories.base import BaseRepository

class EvidenceRepository(BaseRepository[FaceEvidence]):
    def __init__(self, db: Session):
        super().__init__(FaceEvidence, db)

    def get_best_for_track(self, track_id: uuid.UUID) -> Optional[FaceEvidence]:
        stmt = select(FaceEvidence).where(
            FaceEvidence.track_id == track_id,
            FaceEvidence.is_best == True
        )
        return self.db.scalars(stmt).first()

    def list_by_track(self, track_id: uuid.UUID) -> List[FaceEvidence]:
        stmt = select(FaceEvidence).where(FaceEvidence.track_id == track_id).order_by(FaceEvidence.quality_score.desc())
        return list(self.db.scalars(stmt).all())

    def search_evidence(
        self,
        track_id: Optional[uuid.UUID] = None,
        video_id: Optional[uuid.UUID] = None,
        case_id: Optional[uuid.UUID] = None,
        min_quality: Optional[float] = None,
        grade: Optional[str] = None,
        best_only: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[FaceEvidence], int]:
        stmt = select(FaceEvidence)
        count_stmt = select(func.count()).select_from(FaceEvidence)

        if track_id:
            stmt = stmt.where(FaceEvidence.track_id == track_id)
            count_stmt = count_stmt.where(FaceEvidence.track_id == track_id)

        if video_id:
            stmt = stmt.join(PersonTrack, FaceEvidence.track_id == PersonTrack.track_id).where(PersonTrack.video_id == video_id)
            count_stmt = count_stmt.join(PersonTrack, FaceEvidence.track_id == PersonTrack.track_id).where(PersonTrack.video_id == video_id)

        if case_id:
            stmt = stmt.join(CaseEvidence, FaceEvidence.evidence_id == CaseEvidence.evidence_id).where(CaseEvidence.case_id == case_id)
            count_stmt = count_stmt.join(CaseEvidence, FaceEvidence.evidence_id == CaseEvidence.evidence_id).where(CaseEvidence.case_id == case_id)

        if min_quality is not None:
            stmt = stmt.where(FaceEvidence.quality_score >= min_quality)
            count_stmt = count_stmt.where(FaceEvidence.quality_score >= min_quality)

        if grade:
            grade_str = grade.value if hasattr(grade, "value") else str(grade)
            stmt = stmt.where(FaceEvidence.quality_grade == grade_str)
            count_stmt = count_stmt.where(FaceEvidence.quality_grade == grade_str)

        if best_only:
            stmt = stmt.where(FaceEvidence.is_best == True)
            count_stmt = count_stmt.where(FaceEvidence.is_best == True)

        if date_from:
            stmt = stmt.where(FaceEvidence.created_at >= date_from)
            count_stmt = count_stmt.where(FaceEvidence.created_at >= date_from)

        if date_to:
            stmt = stmt.where(FaceEvidence.created_at <= date_to)
            count_stmt = count_stmt.where(FaceEvidence.created_at <= date_to)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.order_by(FaceEvidence.created_at.desc()).offset(offset).limit(limit)).all())
        return items, total

    def search(
        self,
        video_id: Optional[uuid.UUID] = None,
        camera_id: Optional[uuid.UUID] = None,
        track_id: Optional[uuid.UUID] = None,
        case_id: Optional[uuid.UUID] = None,
        is_best: Optional[bool] = None,
        min_quality: Optional[float] = None,
        max_quality: Optional[float] = None,
        quality_grade: Optional[str] = None,
        person_number: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[FaceEvidence], int]:
        offset = (page - 1) * page_size
        return self.search_evidence(
            track_id=track_id,
            video_id=video_id,
            case_id=case_id,
            min_quality=min_quality,
            grade=quality_grade,
            best_only=bool(is_best),
            date_from=start_date,
            date_to=end_date,
            offset=offset,
            limit=page_size
        )

    def promote_candidate_if_best(self, candidate: FaceEvidence) -> bool:
        """
        Atomically evaluates a candidate evidence against the track's current best.
        Uses row locking on PersonTrack to prevent concurrent promotion race conditions.
        Returns True if promoted to best, False otherwise.
        """
        # Lock track row (with_for_update supported under PostgreSQL)
        track_stmt = select(PersonTrack).where(PersonTrack.track_id == candidate.track_id)
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            track_stmt = track_stmt.with_for_update()

        track = self.db.scalars(track_stmt).first()
        if not track:
            return False

        current_best = self.get_best_for_track(candidate.track_id)
        should_promote = False

        if not current_best:
            should_promote = True
        elif candidate.quality_score > current_best.quality_score:
            should_promote = True
        elif candidate.quality_score == current_best.quality_score:
            # Deterministic tie breaking: higher sharpness then earlier frame
            if candidate.sharpness > current_best.sharpness:
                should_promote = True

        if should_promote:
            if current_best and current_best.evidence_id != candidate.evidence_id:
                current_best.is_best = False
                self.db.add(current_best)
                self.db.flush()

            candidate.is_best = True
            self.db.add(candidate)
            self.db.flush()

            track.best_evidence_id = candidate.evidence_id
            self.db.add(track)
            self.db.flush()
            return True

        return False
