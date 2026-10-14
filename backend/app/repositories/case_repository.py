import uuid
from datetime import datetime
from typing import Optional, List, Tuple, Sequence
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from app.models.investigation_case import InvestigationCase, CaseStatus
from app.models.case_evidence import CaseEvidence
from app.repositories.base import BaseRepository

class CaseRepository(BaseRepository[InvestigationCase]):
    def __init__(self, db: Session):
        super().__init__(InvestigationCase, db)

    def create(
        self,
        title: str,
        description: Optional[str] = None,
        status: str = "open",
        assigned_to_id: Optional[uuid.UUID] = None,
        created_by_id: Optional[uuid.UUID] = None
    ) -> InvestigationCase:
        new_case = InvestigationCase(
            title=title,
            description=description,
            status=status,
            assigned_to=assigned_to_id,
            created_by=created_by_id
        )
        self.db.add(new_case)
        self.db.flush()
        return new_case

    def search_cases(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[uuid.UUID] = None,
        created_by: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[InvestigationCase], int]:
        stmt = select(InvestigationCase)
        count_stmt = select(func.count()).select_from(InvestigationCase)

        if query:
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(InvestigationCase.title.ilike(pattern) | InvestigationCase.description.ilike(pattern))
            count_stmt = count_stmt.where(InvestigationCase.title.ilike(pattern) | InvestigationCase.description.ilike(pattern))

        if status:
            stmt = stmt.where(InvestigationCase.status == status)
            count_stmt = count_stmt.where(InvestigationCase.status == status)

        if assigned_to:
            stmt = stmt.where(InvestigationCase.assigned_to == assigned_to)
            count_stmt = count_stmt.where(InvestigationCase.assigned_to == assigned_to)

        if created_by:
            stmt = stmt.where(InvestigationCase.created_by == created_by)
            count_stmt = count_stmt.where(InvestigationCase.created_by == created_by)

        if date_from:
            stmt = stmt.where(InvestigationCase.created_at >= date_from)
            count_stmt = count_stmt.where(InvestigationCase.created_at >= date_from)

        if date_to:
            stmt = stmt.where(InvestigationCase.created_at <= date_to)
            count_stmt = count_stmt.where(InvestigationCase.created_at <= date_to)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.order_by(InvestigationCase.created_at.desc()).offset(offset).limit(limit)).all())
        return items, total

    def search(
        self,
        status: Optional[str] = None,
        assigned_to_id: Optional[uuid.UUID] = None,
        created_by_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[InvestigationCase], int]:
        offset = (page - 1) * page_size
        return self.search_cases(
            query=search,
            status=status,
            assigned_to=assigned_to_id,
            created_by=created_by_id,
            date_from=start_date,
            date_to=end_date,
            offset=offset,
            limit=page_size
        )

    def update(self, case: InvestigationCase, **kwargs) -> InvestigationCase:
        for k, v in kwargs.items():
            if hasattr(case, k):
                setattr(case, k, v)
        self.db.flush()
        return case

    def add_evidence(self, case_id: uuid.UUID, evidence_id: uuid.UUID, added_by_id: Optional[uuid.UUID]) -> CaseEvidence:
        return self.assign_evidence_to_case(case_id, evidence_id, added_by_id)

    def remove_evidence(self, case_id: uuid.UUID, evidence_id: uuid.UUID) -> bool:
        return self.remove_evidence_from_case(case_id, evidence_id)

    def assign_evidence_to_case(self, case_id: uuid.UUID, evidence_id: uuid.UUID, added_by: Optional[uuid.UUID]) -> CaseEvidence:
        existing = self.db.get(CaseEvidence, (case_id, evidence_id))
        if existing:
            return existing
        mapping = CaseEvidence(case_id=case_id, evidence_id=evidence_id, added_by=added_by)
        self.db.add(mapping)
        self.db.flush()
        return mapping

    def remove_evidence_from_case(self, case_id: uuid.UUID, evidence_id: uuid.UUID) -> bool:
        existing = self.db.get(CaseEvidence, (case_id, evidence_id))
        if existing:
            self.db.delete(existing)
            self.db.flush()
            return True
        return False

    def count_active_cases_for_evidence(self, evidence_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(CaseEvidence).where(CaseEvidence.evidence_id == evidence_id)
        return self.db.scalar(stmt) or 0
