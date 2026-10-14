import uuid
from typing import Sequence
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, BusinessRuleException
from app.models.investigation_case import InvestigationCase
from app.models.case_evidence import CaseEvidence
from app.models.user import User
from app.repositories.case_repository import CaseRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.case import CaseCreate, CaseUpdate, CaseFilter


class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_case(self, case_in: CaseCreate, current_user: User) -> InvestigationCase:
        new_case = self.case_repo.create(
            title=case_in.title,
            description=case_in.description,
            status=case_in.status,
            assigned_to_id=case_in.assigned_to_id,
            created_by_id=current_user.id
        )

        self.audit_repo.log_action(
            action="CREATE_CASE",
            resource="InvestigationCase",
            user_id=current_user.id,
            metadata={
                "case_id": str(new_case.id),
                "title": new_case.title,
                "assigned_to_id": str(new_case.assigned_to_id) if new_case.assigned_to_id else None
            }
        )

        return new_case

    def get_by_id(self, case_id: uuid.UUID) -> InvestigationCase:
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundException("InvestigationCase", str(case_id))
        return case

    def list_cases(
        self,
        filters: CaseFilter,
        current_user: User | None = None
    ) -> tuple[Sequence[InvestigationCase], int]:
        return self.case_repo.search(
            status=filters.status,
            assigned_to_id=filters.assigned_to_id,
            created_by_id=filters.created_by_id,
            search=filters.search,
            start_date=filters.start_date,
            end_date=filters.end_date,
            page=filters.page,
            page_size=filters.page_size
        )

    def update_case(
        self,
        case_id: uuid.UUID,
        case_in: CaseUpdate,
        current_user: User
    ) -> InvestigationCase:
        case = self.get_by_id(case_id)

        update_data = case_in.model_dump(exclude_unset=True)
        if not update_data:
            return case

        updated = self.case_repo.update(case, **update_data)

        self.audit_repo.log_action(
            action="UPDATE_CASE",
            resource="InvestigationCase",
            user_id=current_user.id,
            metadata={
                "case_id": str(case_id),
                "updated_fields": list(update_data.keys())
            }
        )

        return updated

    def assign_evidence(
        self,
        case_id: uuid.UUID,
        evidence_ids: list[uuid.UUID],
        current_user: User
    ) -> list[CaseEvidence]:
        case = self.get_by_id(case_id)

        assignments: list[CaseEvidence] = []
        assigned_ids = []

        for ev_id in evidence_ids:
            evidence = self.evidence_repo.get_by_id(ev_id)
            if not evidence:
                raise NotFoundException("FaceEvidence", str(ev_id))

            mapping = self.case_repo.add_evidence(
                case_id=case.id,
                evidence_id=evidence.id,
                added_by_id=current_user.id
            )
            assignments.append(mapping)
            assigned_ids.append(str(ev_id))

        self.audit_repo.log_action(
            action="ASSIGN_CASE_EVIDENCE",
            resource="InvestigationCase",
            user_id=current_user.id,
            metadata={
                "case_id": str(case_id),
                "evidence_ids": assigned_ids
            }
        )

        return assignments

    def remove_evidence(
        self,
        case_id: uuid.UUID,
        evidence_id: uuid.UUID,
        current_user: User
    ) -> bool:
        removed = self.case_repo.remove_evidence(case_id, evidence_id)
        if removed:
            self.audit_repo.log_action(
                action="REMOVE_CASE_EVIDENCE",
                resource="InvestigationCase",
                user_id=current_user.id,
                metadata={
                    "case_id": str(case_id),
                    "evidence_id": str(evidence_id)
                }
            )
        return removed

    def delete_case(self, case_id: uuid.UUID, current_user: User) -> bool:
        case = self.get_by_id(case_id)
        # We do soft-deletion by setting status to archived or deleting the case container
        # Note: Underlying evidence is never deleted when a case is deleted!
        self.case_repo.delete(case)

        self.audit_repo.log_action(
            action="DELETE_CASE",
            resource="InvestigationCase",
            user_id=current_user.id,
            metadata={"case_id": str(case_id), "title": case.title}
        )
        return True
