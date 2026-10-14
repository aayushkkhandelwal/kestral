import os
import uuid
import json
import zipfile
import shutil
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundException, BusinessRuleException
from app.models.investigation_case import InvestigationCase
from app.models.user import User
from app.repositories.case_repository import CaseRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.audit_repository import AuditRepository
from app.utils.time import utc_now


class ExportService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.case_repo = CaseRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.audit_repo = AuditRepository(db)

    def generate_case_dossier(
        self,
        case_id: uuid.UUID,
        exporting_user: User
    ) -> str:
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundException("InvestigationCase", str(case_id))

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        export_folder_name = f"dossier_case_{case.id}_{timestamp_str}"
        temp_export_dir = os.path.join(self.settings.EXPORTS_DIR, export_folder_name)
        os.makedirs(temp_export_dir, exist_ok=True)

        images_dir = os.path.join(temp_export_dir, "evidence_images")
        os.makedirs(images_dir, exist_ok=True)

        # Assemble metadata
        evidence_items = []
        html_evidence_rows = []

        for mapping in case.case_evidence:
            ev = mapping.evidence
            if not ev:
                continue

            track = ev.track
            video = track.video if track else None
            camera = video.camera if video else None

            # Copy image assets if they exist
            full_face_path = self.settings.get_storage_path(ev.face_crop_path)
            full_frame_path = self.settings.get_storage_path(ev.full_frame_path)

            face_rel_copy = None
            frame_rel_copy = None

            if os.path.exists(full_face_path):
                dest_face = os.path.join(images_dir, os.path.basename(full_face_path))
                shutil.copy2(full_face_path, dest_face)
                face_rel_copy = os.path.join("evidence_images", os.path.basename(full_face_path))

            if os.path.exists(full_frame_path):
                dest_frame = os.path.join(images_dir, os.path.basename(full_frame_path))
                shutil.copy2(full_frame_path, dest_frame)
                frame_rel_copy = os.path.join("evidence_images", os.path.basename(full_frame_path))

            ev_dict = {
                "evidence_id": str(ev.id),
                "is_best": ev.is_best,
                "quality_score": ev.quality_score,
                "quality_grade": ev.quality_grade.value if hasattr(ev.quality_grade, 'value') else str(ev.quality_grade),
                "sharpness": ev.sharpness,
                "brightness": ev.brightness,
                "contrast": ev.contrast,
                "confidence": ev.face_confidence,
                "face_hash": ev.face_hash,
                "frame_hash": ev.frame_hash,
                "face_crop_file": face_rel_copy,
                "full_frame_file": frame_rel_copy,
                "track": {
                    "track_id": str(track.id) if track else None,
                    "person_number": track.person_number if track else None,
                    "start_frame": track.start_frame if track else None,
                    "end_frame": track.end_frame if track else None,
                    "total_frames": track.total_frames if track else None
                } if track else None,
                "video": {
                    "video_id": str(video.id) if video else None,
                    "filename": video.filename if video else None,
                    "sha256": video.sha256_hash if video else None
                } if video else None,
                "camera": {
                    "camera_id": str(camera.id) if camera else None,
                    "name": camera.name if camera else None,
                    "location": camera.location if camera else None,
                    "atm_id": camera.atm_id if camera else None
                } if camera else None,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            evidence_items.append(ev_dict)

            html_evidence_rows.append(f"""
            <tr>
                <td>{ev.id}</td>
                <td>{track.person_number if track else 'N/A'}</td>
                <td><strong>{ev.quality_grade.value if hasattr(ev.quality_grade, 'value') else str(ev.quality_grade)}</strong> ({ev.quality_score:.2f})</td>
                <td>{ev.sharpness:.1f} / {ev.brightness:.1f} / {ev.contrast:.1f}</td>
                <td><code>{ev.face_hash[:16]}...</code></td>
                <td>{face_rel_copy or 'Missing'}</td>
            </tr>
            """)

        export_metadata = {
            "dossier_version": "1.0",
            "export_timestamp": utc_now().isoformat(),
            "exported_by": {
                "id": str(exporting_user.id),
                "name": exporting_user.name,
                "email": exporting_user.email,
                "role": exporting_user.role.value if hasattr(exporting_user.role, 'value') else str(exporting_user.role)
            },
            "case": {
                "id": str(case.id),
                "title": case.title,
                "description": case.description,
                "status": case.status.value if hasattr(case.status, 'value') else str(case.status),
                "created_at": case.created_at.isoformat() if case.created_at else None,
                "updated_at": case.updated_at.isoformat() if case.updated_at else None
            },
            "evidence_count": len(evidence_items),
            "evidence_items": evidence_items
        }

        # Write metadata.json
        meta_path = os.path.join(temp_export_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(export_metadata, f, indent=2)

        # Write investigation report HTML
        html_report = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Kestral AI Forensic Dossier - Case {case.id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; color: #1e293b; background: #f8fafc; }}
        .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 24px; }}
        h1 {{ margin: 0 0 8px 0; color: #0f172a; font-size: 24px; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; background: white; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
        th {{ background: #f1f5f9; font-weight: 600; color: #334155; }}
        code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
        .footer {{ margin-top: 32px; font-size: 12px; color: #64748b; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>KESTRAL AI FORENSIC INVESTIGATION DOSSIER</h1>
        <p>Official Digital Evidence Archive & Chain of Custody Report</p>
    </div>
    <div class="meta-grid">
        <div><strong>Case Title:</strong> {case.title}</div>
        <div><strong>Case ID:</strong> {case.id}</div>
        <div><strong>Status:</strong> {case.status.value if hasattr(case.status, 'value') else str(case.status)}</div>
        <div><strong>Exported By:</strong> {exporting_user.name} ({exporting_user.email})</div>
        <div><strong>Export Timestamp:</strong> {utc_now().isoformat()}</div>
        <div><strong>Evidence Count:</strong> {len(evidence_items)}</div>
    </div>
    <h2>Associated Evidence & Hash Audit</h2>
    <table>
        <thead>
            <tr>
                <th>Evidence ID</th>
                <th>Track Person</th>
                <th>Quality Grade</th>
                <th>Metrics (S/B/C)</th>
                <th>Face SHA-256</th>
                <th>Relative Path</th>
            </tr>
        </thead>
        <tbody>
            {''.join(html_evidence_rows) if html_evidence_rows else '<tr><td colspan="6">No evidence linked to this case.</td></tr>'}
        </tbody>
    </table>
    <div class="footer">
        Generated autonomously by Kestral AI Forensic Evidence Engine • Non-repudiable Audit Hash Enforced
    </div>
</body>
</html>"""

        report_path = os.path.join(temp_export_dir, "report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_report)

        # Create zip archive
        zip_filename = f"{export_folder_name}.zip"
        zip_full_path = os.path.join(self.settings.EXPORTS_DIR, zip_filename)

        with zipfile.ZipFile(zip_full_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_export_dir)
                    zipf.write(file_path, arcname)

        # Clean up temporary extracted folder
        shutil.rmtree(temp_export_dir, ignore_errors=True)

        # Record audit log
        self.audit_repo.log_action(
            action="GENERATE_EXPORT",
            resource="InvestigationCase",
            user_id=exporting_user.id,
            metadata={
                "case_id": str(case_id),
                "export_filename": zip_filename,
                "evidence_count": len(evidence_items)
            }
        )

        return zip_filename
