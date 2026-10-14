import os
import zipfile
import pytest
from app.models.video import Video
from app.models.person_track import PersonTrack
from app.models.face_evidence import FaceEvidence
from app.core.config import get_settings


def test_case_lifecycle_and_export(client, investigator_headers, db):
    # Setup video, track, and evidence
    video = Video(
        filename="bank_robbery_cam2.mp4",
        file_path="uploads/bank_robbery_cam2.mp4",
        sha256="1234567890abcdef",
        file_size_bytes=2048,
        processing_status="completed"
    )
    db.add(video)
    db.flush()

    track = PersonTrack(
        video_id=video.video_id,
        person_number=1,
        start_frame=1,
        end_frame=100,
        total_frames=100
    )
    db.add(track)
    db.flush()

    evidence = FaceEvidence(
        track_id=track.track_id,
        face_crop_path="faces/face_sample.jpg",
        full_frame_path="frames/frame_sample.jpg",
        quality_score=92.0,
        quality_grade="HIGH",
        sharpness=88.0,
        brightness=55.0,
        contrast=0.6,
        resolution="200x200",
        face_confidence=0.98,
        sha256_crop="face_hash_sample",
        sha256_frame="frame_hash_sample",
        is_best=True
    )
    db.add(evidence)
    db.commit()

    # 1. Create Case
    create_resp = client.post("/api/v1/cases", headers=investigator_headers, json={
        "title": "Incident #449 - ATM Skimming Investigation",
        "description": "Suspect observed tampering with card reader unit."
    })
    assert create_resp.status_code == 201
    case_data = create_resp.json()
    case_id = case_data["case_id"]

    # 2. Assign Evidence to Case
    assign_resp = client.post(f"/api/v1/cases/{case_id}/assign-evidence", headers=investigator_headers, json={
        "evidence_ids": [str(evidence.evidence_id)]
    })
    assert assign_resp.status_code == 200
    assert assign_resp.json()["assigned_count"] == 1

    # 3. Export Case Dossier
    export_resp = client.post(f"/api/v1/cases/{case_id}/export", headers=investigator_headers)
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert "export_filename" in export_data
    zip_filename = export_data["export_filename"]

    settings = get_settings()
    zip_path = os.path.join(settings.EXPORTS_DIR, zip_filename)
    assert os.path.exists(zip_path)

    # Verify contents of generated ZIP
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        assert any("metadata.json" in n for n in names)
        assert any("report.html" in n for n in names)

    # Clean up test zip file
    if os.path.exists(zip_path):
        os.remove(zip_path)
