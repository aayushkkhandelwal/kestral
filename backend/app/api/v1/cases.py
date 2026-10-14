import os
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_permission
from app.models.user import User
from app.schemas.case import (
    CaseCreate,
    CaseUpdate,
    CaseResponse,
    CaseDetailResponse,
    CaseFilter,
    CaseAssignEvidenceRequest,
    CaseExportResponse
)
from app.schemas.common import PaginatedResponse
from app.services.case_service import CaseService
from app.services.export_service import ExportService
from app.core.config import get_settings

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    case_in: CaseCreate,
    current_user: Annotated[User, Depends(require_permission("cases:write"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = CaseService(db)
    return service.create_case(case_in, current_user=current_user)


@router.get("", response_model=PaginatedResponse[CaseResponse])
def list_cases(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("cases:read"))],
    status: str | None = None,
    assigned_to_id: uuid.UUID | None = None,
    created_by_id: uuid.UUID | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20
):
    service = CaseService(db)
    filters = CaseFilter(
        status=status,
        assigned_to_id=assigned_to_id,
        created_by_id=created_by_id,
        search=search,
        page=page,
        page_size=page_size
    )
    items, total = service.list_cases(filters, current_user=current_user)
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=[CaseResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(
    case_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("cases:read"))]
):
    service = CaseService(db)
    return service.get_by_id(case_id)


@router.put("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: uuid.UUID,
    case_in: CaseUpdate,
    current_user: Annotated[User, Depends(require_permission("cases:write"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = CaseService(db)
    return service.update_case(case_id, case_in, current_user=current_user)


@router.delete("/{case_id}", status_code=status.HTTP_200_OK)
def delete_case(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_permission("cases:write"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = CaseService(db)
    service.delete_case(case_id, current_user=current_user)
    return {"message": "Case archived or deleted successfully", "case_id": str(case_id)}


@router.post("/{case_id}/assign-evidence", status_code=status.HTTP_200_OK)
def assign_evidence(
    case_id: uuid.UUID,
    assign_in: CaseAssignEvidenceRequest,
    current_user: Annotated[User, Depends(require_permission("cases:write"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = CaseService(db)
    mappings = service.assign_evidence(case_id, assign_in.evidence_ids, current_user=current_user)
    return {
        "message": f"Successfully associated {len(mappings)} evidence items with case",
        "case_id": str(case_id),
        "assigned_count": len(mappings)
    }


@router.delete("/{case_id}/evidence/{evidence_id}", status_code=status.HTTP_200_OK)
def remove_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_permission("cases:write"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = CaseService(db)
    service.remove_evidence(case_id, evidence_id, current_user=current_user)
    return {"message": "Evidence disassociated from case", "evidence_id": str(evidence_id)}


@router.post("/{case_id}/export", response_model=CaseExportResponse)
def export_case(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_permission("evidence:export"))],
    db: Annotated[Session, Depends(get_db)]
):
    export_service = ExportService(db)
    filename = export_service.generate_case_dossier(case_id, exporting_user=current_user)
    download_url = f"/api/v1/cases/export/download/{filename}"
    return CaseExportResponse(
        case_id=case_id,
        export_filename=filename,
        download_url=download_url,
        message="Forensic case dossier generated successfully with cryptographic audit hashes."
    )


@router.get("/export/download/{filename}")
def download_export(
    filename: str,
    current_user: Annotated[User, Depends(require_permission("evidence:export"))]
):
    settings = get_settings()
    # Sanitize and validate filename to prevent path traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(settings.EXPORTS_DIR, safe_filename)
    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Export dossier file not found")

    return FileResponse(
        path=file_path,
        media_type="application/zip",
        filename=safe_filename
    )
