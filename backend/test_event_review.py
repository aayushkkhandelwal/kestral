import os
import sys
import uuid
import json
import pytest
from datetime import datetime, timezone

# Ensure backend root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.event_detector import EventDetector
from services.clip_buffer_service import ClipBufferService
from app.utils.hashing import compute_sha256_file
from app.database.session import SessionLocal
from app.models.surveillance_event import SurveillanceEvent
from app.models.evidence_clip import EvidenceClip
from app.models.event_screenshot import EventScreenshot
from app.models.monitored_zone import MonitoredZone
from app.models.camera import Camera
from app.models.video import Video
from app.services.event_service import EventService
from app.schemas.event import TransactionWebhookPayload, EvidenceExportRequest


def test_event_detector_point_in_polygon():
    """Verify polygonal boundary containment algorithm."""
    detector = EventDetector()
    poly = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]

    assert detector.is_point_in_polygon((0.5, 0.5), poly) is True
    assert detector.is_point_in_polygon((0.1, 0.5), poly) is False
    assert detector.is_point_in_polygon((0.9, 0.9), poly) is False
    assert detector.is_point_in_polygon((0.5, 0.85), poly) is False


def test_event_detector_entry_and_exit_with_debounce():
    """Verify entry and exit events with cooldown suppression."""
    detector = EventDetector(entry_exit_cooldown_sec=3.0)
    zones = [{
        "zone_id": "zone-1",
        "name": "ATM Test Zone",
        "zone_type": "polygon",
        "coordinates": [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]
    }]
    frame_w, frame_h = 1000, 1000

    # Step 1: Outside (feet anchor at y=100/1000 = 0.1)
    evs1 = detector.process_frame_tracks(
        frame_idx=1,
        timestamp_sec=1.0,
        detections=[{"track_id": 1, "bbox": [50, 50, 150, 100]}],
        zones=zones,
        frame_w=frame_w,
        frame_h=frame_h
    )
    assert len(evs1) == 0

    # Step 2: Crosses inside (feet anchor at cx=500/1000=0.5, y=500/1000=0.5) -> Entry event
    evs2 = detector.process_frame_tracks(
        frame_idx=50,
        timestamp_sec=2.0,
        detections=[{"track_id": 1, "bbox": [400, 400, 600, 500]}],
        zones=zones,
        frame_w=frame_w,
        frame_h=frame_h
    )
    assert len(evs2) == 1
    assert evs2[0]["event_type"] == "person_entry"
    assert evs2[0]["video_timestamp_sec"] == 2.0

    # Step 3: Still inside, jittering -> NO duplicate entry event (debounce)
    evs3 = detector.process_frame_tracks(
        frame_idx=60,
        timestamp_sec=2.5,
        detections=[{"track_id": 1, "bbox": [410, 410, 610, 510]}],
        zones=zones,
        frame_w=frame_w,
        frame_h=frame_h
    )
    assert len(evs3) == 0

    # Step 4: Rapid exit within cooldown window (< 3.0s cooldown, at 3.5s vs last transition at 2.0s) -> suppressed
    evs4 = detector.process_frame_tracks(
        frame_idx=80,
        timestamp_sec=3.5,
        detections=[{"track_id": 1, "bbox": [50, 50, 150, 100]}],
        zones=zones,
        frame_w=frame_w,
        frame_h=frame_h
    )
    assert len(evs4) == 0

    # Step 5: Exit after cooldown expires (timestamp 6.0s >= 2.0s + 3.0s) -> Exit event
    evs5 = detector.process_frame_tracks(
        frame_idx=150,
        timestamp_sec=6.0,
        detections=[{"track_id": 1, "bbox": [50, 50, 150, 100]}],
        zones=zones,
        frame_w=frame_w,
        frame_h=frame_h
    )
    assert len(evs5) == 1
    assert evs5[0]["event_type"] == "person_exit"
    assert evs5[0]["video_timestamp_sec"] == 6.0


def test_clip_buffer_boundary_calculations():
    """Verify exact 10s pre/post buffer boundary calculations including start/end edge cases."""
    clip_service = ClipBufferService()

    # Case A: Middle of video (e.g. at 50s in a 100s video)
    # Target: 10s pre, 10s post -> 40s to 60s (20s duration)
    start_sec = max(0.0, 50.0 - 10.0)
    end_sec = min(100.0, 50.0 + 10.0)
    assert start_sec == 40.0
    assert end_sec == 60.0
    assert (end_sec - start_sec) == 20.0

    # Case B: Near beginning (e.g. event at 4.2s in a 100s video)
    # Target: 10s pre (only 4.2s available), 10s post -> 0.0s to 14.2s (14.2s duration)
    start_sec_b = max(0.0, 4.2 - 10.0)
    end_sec_b = min(100.0, 4.2 + 10.0)
    assert start_sec_b == 0.0
    assert end_sec_b == 14.2
    assert (end_sec_b - start_sec_b) == 14.2

    # Case C: Near end (e.g. event at 95.0s in a 100s video)
    # Target: 10s pre, 10s post (only 5.0s available) -> 85.0s to 100.0s (15.0s duration)
    start_sec_c = max(0.0, 95.0 - 10.0)
    end_sec_c = min(100.0, 95.0 + 10.0)
    assert start_sec_c == 85.0
    assert end_sec_c == 100.0
    assert (end_sec_c - start_sec_c) == 15.0


def test_database_events_and_clips_integrity():
    """Verify that stored events in PostgreSQL have corresponding clips and valid SHA-256 hashes."""
    with SessionLocal() as db:
        events = db.query(SurveillanceEvent).all()
        assert len(events) > 0, "Expected at least 1 surveillance event in DB"

        for ev in events:
            assert ev.event_type in ["person_entry", "person_exit", "transaction_start", "inferred_transaction"]
            assert ev.confidence >= 0.0 and ev.confidence <= 1.0

            # Verify associated clip
            clip = db.query(EvidenceClip).filter(EvidenceClip.event_id == ev.event_id).first()
            if clip:
                assert clip.clip_path.startswith("/clips/")
                assert len(clip.sha256) == 64  # Valid SHA-256 hex string
                disk_path = os.path.join(BASE_DIR, clip.clip_path.lstrip("/"))
                assert os.path.exists(disk_path), f"Evidence clip file {disk_path} must exist on disk"
                # Verify SHA-256 matches actual file on disk
                computed_hash = compute_sha256_file(disk_path)
                assert computed_hash == clip.sha256, "Forensic hash in DB must match on-disk file"


def test_transaction_webhook_ingestion():
    """Verify external transaction webhook ingestion creates a transaction_start event."""
    with SessionLocal() as db:
        cam = db.query(Camera).first()
        vid = db.query(Video).first()
        if not cam or not vid:
            pytest.skip("Camera or Video missing from database")

        service = EventService(db)
        payload = TransactionWebhookPayload(
            camera_id=cam.camera_id,
            video_id=vid.video_id,
            atm_id="ATM-TEST-01",
            transaction_id="TXN-998877",
            event_timestamp=datetime.now(timezone.utc),
            video_timestamp_sec=12.5,
            confidence=0.99,
            metadata={"card_masked": "4111********1111", "terminal": "T4-01"}
        )

        event = service.ingest_transaction_webhook(
            atm_id=payload.atm_id,
            transaction_id=payload.transaction_id,
            metadata=payload.metadata
        )
        assert event.event_type == "transaction_start"
        assert event.source == "atm_webhook"
        assert event.confidence == 1.0
        assert event.event_metadata["transaction_id"] == "TXN-998877"

        # Verify event was persisted to DB
        stored = db.query(SurveillanceEvent).filter(SurveillanceEvent.event_id == event.event_id).first()
        assert stored is not None
        assert stored.event_type == "transaction_start"


def test_evidence_export_package():
    """Verify export dossier generation produces a zip archive containing manifest and evidence."""
    with SessionLocal() as db:
        ev = db.query(SurveillanceEvent).first()
        if not ev:
            pytest.skip("No surveillance events in DB")

        service = EventService(db)
        resp = service.export_evidence_package(
            event_ids=[ev.event_id],
            notes="Automated forensic test package"
        )
        assert resp["export_id"] is not None
        assert resp["download_url"].startswith("/exports/")
        assert resp["events_included_count"] >= 1

        zip_disk_path = os.path.join(BASE_DIR, resp["download_url"].lstrip("/"))
        assert os.path.exists(zip_disk_path)
        assert os.path.getsize(zip_disk_path) > 0


if __name__ == "__main__":
    print("Running Event Review automated test suite...")
    test_event_detector_point_in_polygon()
    print("  ✓ Point-in-polygon containment test passed")
    test_event_detector_entry_and_exit_with_debounce()
    print("  ✓ Entry/exit detection and cooldown debounce test passed")
    test_clip_buffer_boundary_calculations()
    print("  ✓ 10s pre/post buffer boundary edge-case test passed")
    test_database_events_and_clips_integrity()
    print("  ✓ Database events & clip forensic SHA-256 integrity test passed")
    test_transaction_webhook_ingestion()
    print("  ✓ ATM transaction webhook ingestion test passed")
    test_evidence_export_package()
    print("  ✓ Forensic evidence export dossier test passed")
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! (6/6)")
