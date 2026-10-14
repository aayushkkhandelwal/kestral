import uuid
import pytest
from app.models.video import Video
from app.models.person_track import PersonTrack
from app.models.face_evidence import FaceEvidence
from app.repositories.evidence_repository import EvidenceRepository


def test_atomic_best_evidence_promotion(db):
    # Setup test video and track
    video = Video(
        filename="test_surveillance.mp4",
        file_path="uploads/test_surveillance.mp4",
        sha256="abcdef1234567890",
        file_size_bytes=1024,
        processing_status="completed"
    )
    db.add(video)
    db.flush()

    track = PersonTrack(
        video_id=video.video_id,
        person_number=1,
        start_frame=10,
        end_frame=150,
        total_frames=140
    )
    db.add(track)
    db.flush()

    repo = EvidenceRepository(db)

    # 1. Candidate 1: Quality score 65.0
    cand1 = FaceEvidence(
        track_id=track.track_id,
        face_crop_path="faces/cand1.jpg",
        full_frame_path="frames/frame1.jpg",
        quality_score=65.0,
        quality_grade="MEDIUM",
        sharpness=60.0,
        brightness=50.0,
        contrast=0.5,
        resolution="120x120",
        face_confidence=0.85,
        sha256_crop="hash1",
        sha256_frame="frame_hash1",
        is_best=False
    )
    db.add(cand1)
    db.flush()

    promoted1 = repo.promote_candidate_if_best(cand1)
    assert promoted1 is True
    assert cand1.is_best is True
    assert track.best_evidence_id == cand1.evidence_id

    # 2. Candidate 2: Quality score 50.0 (lower than 65.0 -> should NOT displace)
    cand2 = FaceEvidence(
        track_id=track.track_id,
        face_crop_path="faces/cand2.jpg",
        full_frame_path="frames/frame2.jpg",
        quality_score=50.0,
        quality_grade="LOW",
        sharpness=45.0,
        brightness=50.0,
        contrast=0.5,
        resolution="100x100",
        face_confidence=0.80,
        sha256_crop="hash2",
        sha256_frame="frame_hash2",
        is_best=False
    )
    db.add(cand2)
    db.flush()

    promoted2 = repo.promote_candidate_if_best(cand2)
    assert promoted2 is False
    assert cand2.is_best is False
    # Cand1 remains best
    assert cand1.is_best is True
    assert track.best_evidence_id == cand1.evidence_id

    # 3. Candidate 3: Quality score 88.5 (higher -> should promote and demote cand1)
    cand3 = FaceEvidence(
        track_id=track.track_id,
        face_crop_path="faces/cand3.jpg",
        full_frame_path="frames/frame3.jpg",
        quality_score=88.5,
        quality_grade="HIGH",
        sharpness=85.0,
        brightness=52.0,
        contrast=0.6,
        resolution="180x180",
        face_confidence=0.96,
        sha256_crop="hash3",
        sha256_frame="frame_hash3",
        is_best=False
    )
    db.add(cand3)
    db.flush()

    promoted3 = repo.promote_candidate_if_best(cand3)
    assert promoted3 is True
    assert cand3.is_best is True
    assert cand1.is_best is False
    assert cand2.is_best is False
    assert track.best_evidence_id == cand3.evidence_id

    # Verify all 3 records are retained in database history
    all_evidence = repo.list_by_track(track.track_id)
    assert len(all_evidence) == 3
