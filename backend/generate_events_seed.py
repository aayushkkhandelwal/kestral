import os
import sys
import json
import uuid
import cv2
from datetime import datetime, timezone

sys.path.insert(0, ".")

from app.database.session import SessionLocal
from app.models.video import Video
from app.models.camera import Camera
from app.models.person_track import PersonTrack
from app.models.surveillance_event import SurveillanceEvent
from app.models.evidence_clip import EvidenceClip
from app.models.monitored_zone import MonitoredZone
from services.clip_buffer_service import ClipBufferService
from app.utils.hashing import compute_sha256_file

video_path = r"uploads/74d46b67_sample.mp4"
results_json = r"results/74d46b67/results.json"

if not os.path.exists(video_path) or not os.path.exists(results_json):
    print("Files missing!")
    sys.exit(1)

with open(results_json, "r") as f:
    res = json.load(f)

clip_service = ClipBufferService()

with SessionLocal() as db:
    # Ensure default Camera exists
    cam = db.query(Camera).filter(Camera.camera_name == "ATM-04 Main Vestibule").first()
    if not cam:
        cam = Camera(
            camera_name="ATM-04 Main Vestibule",
            atm_id="ATM-NYC-04",
            location="Terminal 4, Concourse B",
            status="online"
        )
        db.add(cam)
        db.flush()

    # Ensure default Monitored Zone exists
    zone = db.query(MonitoredZone).filter(MonitoredZone.name == "ATM Interaction Zone").first()
    if not zone:
        zone = MonitoredZone(
            name="ATM Interaction Zone",
            zone_type="polygon",
            camera_id=cam.camera_id,
            coordinates=[[0.10, 0.30], [0.90, 0.30], [0.90, 0.95], [0.10, 0.95]],
            is_active=True
        )
        db.add(zone)
        db.flush()

    # Ensure Video record exists
    vid = db.query(Video).filter(Video.filename.like("%74d46b67%")).first()
    if not vid:
        file_hash = compute_sha256_file(video_path)
        vid = Video(
            camera_id=cam.camera_id,
            filename=os.path.basename(video_path),
            file_path=f"/uploads/{os.path.basename(video_path)}",
            file_size_bytes=os.path.getsize(video_path),
            duration=float(res["metadata"]["duration_seconds"]),
            fps=float(res["metadata"]["fps"]),
            resolution=str(res["metadata"]["resolution"]),
            sha256=file_hash,
            processing_status="completed",
            processed_at=datetime.now(timezone.utc)
        )
        db.add(vid)
        db.flush()

    # Clear old events for this video to ensure clean idempotent generation
    existing_events = db.query(SurveillanceEvent).filter(SurveillanceEvent.video_id == vid.video_id).all()
    for ev in existing_events:
        db.delete(ev)
    db.commit()

    tracks = res.get("tracks", [])
    print(f"Generating events for {len(tracks)} consolidated tracks...")

    created_events = []
    for t in tracks:
        p_num = int(t["track_id"])
        # Ensure PersonTrack exists
        ptrack = db.query(PersonTrack).filter(
            PersonTrack.video_id == vid.video_id,
            PersonTrack.person_number == p_num
        ).first()
        if not ptrack:
            ptrack = PersonTrack(
                video_id=vid.video_id,
                person_number=p_num,
                start_frame=int(t.get("best_frame_idx", 0)),
                end_frame=int(t.get("best_frame_idx", 0)),
                total_frames=int(t.get("total_detections", 1))
            )
            db.add(ptrack)
            db.flush()

        # Define 2-3 key events per subject
        t_entry = float(t["first_seen_time"])
        t_exit = float(t["last_seen_time"])
        t_tx = float(t.get("best_timestamp", (t_entry + t_exit) / 2.0))

        events_to_create = [
            {
                "type": "person_entry",
                "time": t_entry,
                "confidence": 0.95,
                "source": "vision_analytics",
                "desc": f"Subject #{p_num} entered monitored ATM area"
            },
            {
                "type": "transaction_start",
                "time": t_tx,
                "confidence": 0.88,
                "source": "inferred_rule",
                "desc": f"Subject #{p_num} initiated ATM interface session"
            },
            {
                "type": "person_exit",
                "time": t_exit,
                "confidence": 0.92,
                "source": "vision_analytics",
                "desc": f"Subject #{p_num} departed monitored ATM area"
            }
        ]

        for ev_meta in events_to_create:
            ev_id = uuid.uuid4()
            event_obj = SurveillanceEvent(
                event_id=ev_id,
                camera_id=cam.camera_id,
                video_id=vid.video_id,
                track_id=ptrack.track_id,
                zone_id=zone.zone_id,
                person_number=p_num,
                zone_name=zone.name,
                event_type=ev_meta["type"],
                video_timestamp_sec=round(ev_meta["time"], 2),
                source_frame=int(round(ev_meta["time"] * vid.fps)),
                confidence=ev_meta["confidence"],
                source=ev_meta["source"],
                event_metadata={"description": ev_meta["desc"], "consolidated_ids": t.get("consolidated_track_ids", [p_num])},
                processing_status="completed"
            )
            db.add(event_obj)
            db.flush()

            # Generate 10-second pre/post clip buffer
            clip_res = clip_service.extract_event_clip(
                video_path=video_path,
                event_timestamp_sec=ev_meta["time"],
                event_id=str(ev_id),
                pre_event_target_sec=10.0,
                post_event_target_sec=10.0
            )

            clip_obj = EvidenceClip(
                clip_id=uuid.uuid4(),
                event_id=ev_id,
                video_id=vid.video_id,
                clip_path=clip_res["clip_path"],
                clip_start_sec=clip_res["clip_start_sec"],
                clip_end_sec=clip_res["clip_end_sec"],
                pre_event_duration=clip_res["pre_event_duration"],
                post_event_duration=clip_res["post_event_duration"],
                sha256=clip_res["sha256"],
                file_size_bytes=clip_res["file_size_bytes"],
                export_status="available"
            )
            db.add(clip_obj)
            db.flush()
            created_events.append((ev_meta["type"], p_num, ev_meta["time"], clip_res["total_clip_duration"]))

    db.commit()
    print(f"Successfully generated {len(created_events)} events with 10s pre/post buffers!")
    for ev in created_events:
        print(f"  - {ev[0].upper()} (Subject #{ev[1]} at {ev[2]:.1f}s) -> Clip Duration: {ev[3]:.1f}s")
