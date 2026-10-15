import os
import uuid
import json
import shutil
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Paths setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
import sys
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.video_processor import VideoProcessor
from services.person_detector import PersonDetector
from services.face_detector import FaceDetector
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
# Storage folders
FACES_DIR = os.path.join(BASE_DIR, "faces")
FRAMES_DIR = os.path.join(BASE_DIR, "frames")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
CLIPS_DIR = os.path.join(BASE_DIR, "clips")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

app = FastAPI(
    title="Kestral Video Intelligence & Best-Frame Evidence API",
    description="Automated Person Tracking, Face Detection, and Biometric Evidence Extraction",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for video playback and evidence frames
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/faces", StaticFiles(directory=FACES_DIR), name="faces")
app.mount("/frames", StaticFiles(directory=FRAMES_DIR), name="frames")
app.mount("/exports", StaticFiles(directory=EXPORTS_DIR), name="exports")
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="clips")

# Include Clean Architecture Enterprise API V1 Router
try:
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    print(f"[Warning] Failed to mount Enterprise API V1 router: {e}")

from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    DomainException,
    EntityNotFoundException,
    AuthenticationFailedException,
    PermissionDeniedException,
    DuplicateEntityException,
    ValidationException,
    BusinessRuleException
)

@app.exception_handler(EntityNotFoundException)
async def not_found_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(status_code=404, content={"detail": exc.message, "error_code": "NOT_FOUND"})

@app.exception_handler(AuthenticationFailedException)
async def auth_failed_handler(request: Request, exc: AuthenticationFailedException):
    return JSONResponse(status_code=401, content={"detail": exc.message, "error_code": "UNAUTHORIZED"})

@app.exception_handler(PermissionDeniedException)
async def forbidden_handler(request: Request, exc: PermissionDeniedException):
    return JSONResponse(status_code=403, content={"detail": exc.message, "error_code": "FORBIDDEN"})

@app.exception_handler(DuplicateEntityException)
async def duplicate_handler(request: Request, exc: DuplicateEntityException):
    return JSONResponse(status_code=409, content={"detail": exc.message, "error_code": "CONFLICT"})

@app.exception_handler(ValidationException)
async def validation_handler(request: Request, exc: ValidationException):
    return JSONResponse(status_code=422, content={"detail": exc.message, "error_code": "VALIDATION_ERROR"})

@app.exception_handler(BusinessRuleException)
async def business_rule_handler(request: Request, exc: BusinessRuleException):
    return JSONResponse(status_code=400, content={"detail": exc.message, "error_code": "BUSINESS_RULE_VIOLATION"})

# Thread pool for CPU/GPU heavy vision tasks
executor = ThreadPoolExecutor(max_workers=2)

# In-memory task registry
TASKS: Dict[str, Dict[str, Any]] = {}

def sync_process_video_wrapper(task_id: str, video_path: str, output_dir: str):
    """Worker function executed in thread pool."""
    def on_progress(p: Dict[str, Any]):
        if task_id in TASKS:
            TASKS[task_id].update(p)

    try:
        processor = VideoProcessor(confidence_threshold=0.35)
        results = processor.process_video(
            video_path=video_path,
            output_dir=output_dir,
            task_id=task_id,
            progress_callback=on_progress
        )
        TASKS[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "progress": 100.0,
            "result": results
        }

        # Database persistence sync
        try:
            from app.database.session import SessionLocal
            from app.models.video import Video
            from app.models.person_track import PersonTrack
            from app.models.face_evidence import FaceEvidence
            from app.repositories.evidence_repository import EvidenceRepository
            from app.utils.hashing import calculate_sha256
            from datetime import timezone

            with SessionLocal() as db:
                meta = results.get("metadata", {})
                vid = db.query(Video).filter(Video.filename.like(f"%{task_id}%")).first()
                if not vid:
                    rel_vid_path = os.path.relpath(video_path, BASE_DIR).replace("\\", "/")
                    vid_hash = results.get("integrity", {}).get("original_video", {}).get("sha256") or (calculate_sha256(video_path) if os.path.exists(video_path) else None)
                    vid = Video(
                        filename=os.path.basename(video_path),
                        file_path=rel_vid_path,
                        file_size_bytes=os.path.getsize(video_path) if os.path.exists(video_path) else 0,
                        sha256=vid_hash
                    )
                    db.add(vid)
                    db.flush()

                vid.duration = float(meta.get("duration_seconds", 0.0))
                vid.fps = float(meta.get("fps", 0.0))
                vid.resolution = str(meta.get("resolution", "unknown"))
                vid.processing_status = "completed"
                vid.processed_at = datetime.now(timezone.utc)
                db.flush()

                ev_repo = EvidenceRepository(db)
                for t_item in results.get("tracks", []):
                    p_num = int(t_item.get("track_id", 0))
                    track = db.query(PersonTrack).filter(
                        PersonTrack.video_id == vid.video_id,
                        PersonTrack.person_number == p_num
                    ).first()
                    if not track:
                        track = PersonTrack(
                            video_id=vid.video_id,
                            person_number=p_num,
                            start_frame=int(t_item.get("best_frame_idx", 0)),
                            end_frame=int(t_item.get("best_frame_idx", 0)),
                            total_frames=int(t_item.get("total_detections", 1))
                        )
                        db.add(track)
                        db.flush()

                    crop_url = str(t_item.get("crop_url", ""))
                    frame_url = str(t_item.get("full_frame_url", ""))
                    crop_abs = os.path.join(BASE_DIR, crop_url.lstrip("/"))
                    frame_abs = os.path.join(BASE_DIR, frame_url.lstrip("/"))

                    crop_hash = t_item.get("face_sha256") or (calculate_sha256(crop_abs) if os.path.exists(crop_abs) else None)
                    frame_hash = t_item.get("full_frame_sha256") or (calculate_sha256(frame_abs) if os.path.exists(frame_abs) else None)

                    evidence = FaceEvidence(
                        track_id=track.track_id,
                        face_crop_path=crop_url,
                        full_frame_path=frame_url,
                        quality_score=float(t_item.get("quality_score", 0.0)),
                        quality_grade=str(t_item.get("quality", {}).get("grade", "C")),
                        sharpness=float(t_item.get("sharpness_score", 0.0)),
                        brightness=float(t_item.get("exposure_score", 0.0)),
                        contrast=0.5,
                        resolution=f"{t_item.get('quality', {}).get('crop_width', 0)}x{t_item.get('quality', {}).get('crop_height', 0)}",
                        face_confidence=float(t_item.get("face_confidence", 0.0)) if t_item.get("face_confidence") is not None else 0.0,
                        sha256_crop=crop_hash,
                        sha256_frame=frame_hash,
                        is_best=False
                    )
                    db.add(evidence)
                    db.flush()

                    ev_repo.promote_candidate_if_best(evidence)

                db.commit()
                print(f"[DB Sync] Successfully persisted task {task_id} analysis to PostgreSQL.")
        except Exception as db_exc:
            print(f"[DB Sync Warning] Failed to persist task {task_id} results to DB: {db_exc}")
    except Exception as e:
        print(f"[Worker Error] Task {task_id} failed: {e}")
        TASKS[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "progress": 0.0,
            "error": str(e)
        }

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "Kestral Evidence Engine",
        "version": "1.0.0",
        "cuda_available": False
    }

import re

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB limit

@app.post("/api/upload-and-process")
async def upload_and_process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Receives an uploaded video, initiates YOLO tracking & best-frame extraction in background.
    Validates file extension, size limit, and prevents directory traversal.
    """
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=400, detail="Empty filename provided.")

    clean_filename = os.path.basename(file.filename.strip())
    ext = os.path.splitext(clean_filename)[1].lower()

    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"
        )

    task_id = str(uuid.uuid4())[:8]
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean_filename)
    saved_filename = f"{task_id}_{safe_name}"
    video_path = os.path.join(UPLOADS_DIR, saved_filename)
    output_dir = os.path.join(RESULTS_DIR, task_id)

    # Read and stream chunk-by-chunk while enforcing MAX_UPLOAD_SIZE
    total_bytes = 0
    try:
        with open(video_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024) # 1MB chunks
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Video file exceeds maximum allowed size of 500MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        if os.path.exists(video_path):
            os.remove(video_path)
        raise
    except Exception as e:
        if os.path.exists(video_path):
            os.remove(video_path)
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")

    if total_bytes == 0:
        if os.path.exists(video_path):
            os.remove(video_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    TASKS[task_id] = {
        "task_id": task_id,
        "filename": clean_filename,
        "video_url": f"/uploads/{saved_filename}",
        "status": "queued",
        "progress": 0.0,
        "tracks_count": 0,
        "current_frame": 0,
        "total_frames": 0,
        "processing_fps": 0.0
    }

    # Dispatch to background thread pool
    background_tasks.add_task(
        sync_process_video_wrapper,
        task_id=task_id,
        video_path=video_path,
        output_dir=output_dir
    )

    return {
        "task_id": task_id,
        "filename": clean_filename,
        "status": "processing",
        "message": "Video queued for analysis"
    }

@app.get("/api/tasks/{task_id}/status")
def get_task_status(task_id: str):
    """Returns real-time progress of a video analysis task with path sanitization."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    if task_id not in TASKS:
        # Check if saved on disk from previous session
        saved_json = os.path.join(RESULTS_DIR, task_id, "results.json")
        if os.path.exists(saved_json):
            try:
                with open(saved_json, "r") as f:
                    data = json.load(f)
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "progress": 100.0,
                    "result": data
                }
            except Exception:
                pass
        raise HTTPException(status_code=404, detail="Task not found")

    return TASKS[task_id]

@app.get("/api/tasks/{task_id}/results")
def get_task_results(task_id: str):
    """Fetches detailed evidence tracks and metadata for a completed task with path sanitization."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    saved_json = os.path.join(RESULTS_DIR, task_id, "results.json")
    if os.path.exists(saved_json):
        try:
            with open(saved_json, "r") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read results file: {str(e)}")

    if task_id in TASKS and TASKS[task_id].get("status") == "completed":
        return TASKS[task_id].get("result")

    if task_id in TASKS:
        return {"status": TASKS[task_id]["status"], "progress": TASKS[task_id]["progress"]}

    raise HTTPException(status_code=404, detail="Task result not found")

@app.get("/api/tasks/{task_id}/verify-integrity")
def verify_task_integrity(task_id: str):
    """
    Cryptographically verifies the SHA-256 hashes of original uploaded video and
    extracted evidence frames against the immutable manifest stored in results.json.
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    saved_json = os.path.join(RESULTS_DIR, task_id, "results.json")
    if not os.path.exists(saved_json):
        raise HTTPException(status_code=404, detail="Task results not found.")

    try:
        with open(saved_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read results file: {str(e)}")

    integrity = data.get("integrity")
    if not integrity:
        return {
            "task_id": task_id,
            "verified": False,
            "status": "NO_INTEGRITY_DATA",
            "message": "Task was processed prior to integrity ledger implementation.",
            "summary": {
                "total_files_checked": 0,
                "matched": 0,
                "modified": 0,
                "missing": 0
            },
            "evidence_files": []
        }

    from evaluation.metrics import compute_sha256

    results_check = []
    total_checked = 0
    matched_count = 0
    modified_count = 0
    missing_count = 0

    # 1. Verify original video
    orig_vid = integrity.get("original_video", {})
    recorded_vid_path = orig_vid.get("file_path", "")
    recorded_vid_hash = orig_vid.get("sha256", "")

    vid_path_to_check = recorded_vid_path
    if not os.path.exists(vid_path_to_check):
        fallback_vid_path = os.path.join(UPLOADS_DIR, os.path.basename(recorded_vid_path))
        if os.path.exists(fallback_vid_path):
            vid_path_to_check = fallback_vid_path

    vid_status = "MISSING"
    actual_vid_hash = None
    if os.path.exists(vid_path_to_check):
        actual_vid_hash = compute_sha256(vid_path_to_check)
        vid_status = "MATCH" if actual_vid_hash.lower() == recorded_vid_hash.lower() else "MODIFIED"

    total_checked += 1
    if vid_status == "MATCH":
        matched_count += 1
    elif vid_status == "MODIFIED":
        modified_count += 1
    else:
        missing_count += 1

    orig_vid_result = {
        "item_type": "original_video",
        "file_name": os.path.basename(recorded_vid_path),
        "recorded_hash": recorded_vid_hash,
        "calculated_hash": actual_vid_hash,
        "status": vid_status,
        "is_valid": (vid_status == "MATCH")
    }

    # 2. Verify evidence frames
    task_results_dir = os.path.join(RESULTS_DIR, task_id)
    evidence_items = integrity.get("evidence_files", [])
    for ev in evidence_items:
        filename = ev.get("filename")
        expected_hash = ev.get("sha256", "")
        filepath = os.path.join(task_results_dir, filename)

        item_status = "MISSING"
        actual_hash = None
        if os.path.exists(filepath):
            actual_hash = compute_sha256(filepath)
            item_status = "MATCH" if actual_hash.lower() == expected_hash.lower() else "MODIFIED"

        total_checked += 1
        if item_status == "MATCH":
            matched_count += 1
        elif item_status == "MODIFIED":
            modified_count += 1
        else:
            missing_count += 1

        results_check.append({
            "item_type": "evidence_crop",
            "file_name": filename,
            "url": ev.get("url"),
            "recorded_hash": expected_hash,
            "calculated_hash": actual_hash,
            "status": item_status,
            "is_valid": (item_status == "MATCH")
        })

    is_all_valid = (modified_count == 0 and missing_count == 0 and matched_count > 0)
    overall_status = "VERIFIED" if is_all_valid else ("MODIFIED" if modified_count > 0 else "EVIDENCE_MISSING")

    return {
        "task_id": task_id,
        "verified": is_all_valid,
        "status": overall_status,
        "verified_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_files_checked": total_checked,
            "matched": matched_count,
            "modified": modified_count,
            "missing": missing_count
        },
        "original_video": orig_vid_result,
        "evidence_files": results_check,
        "models_used": integrity.get("models_used", {}),
        "disclaimer": integrity.get("disclaimer", "Cryptographic hashes verify bitwise integrity and detect subsequent alteration. They do not independently verify legal chain of custody or capture origin.")
    }

@app.get("/api/history")
def get_analysis_history():
    """Lists all historical analyses and summaries saved in the results directory."""
    history = []
    if not os.path.exists(RESULTS_DIR):
        return history

    for folder_name in os.listdir(RESULTS_DIR):
        task_dir = os.path.join(RESULTS_DIR, folder_name)
        if os.path.isdir(task_dir):
            json_file = os.path.join(task_dir, "results.json")
            if os.path.exists(json_file):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                        # Match video file in uploads
                        video_filename = None
                        video_url = None
                        if os.path.exists(UPLOADS_DIR):
                            for u_file in os.listdir(UPLOADS_DIR):
                                if u_file.startswith(folder_name):
                                    video_filename = u_file[len(folder_name) + 1:]
                                    video_url = f"/uploads/{u_file}"
                                    break

                        file_mtime = os.path.getmtime(json_file)
                        tracks = data.get("tracks", [])

                        history.append({
                            "task_id": data.get("task_id", folder_name),
                            "filename": video_filename or data.get("filename") or data.get("metadata", {}).get("filename") or f"cctv_{folder_name}.mp4",
                            "video_url": video_url or data.get("video_url"),
                            "timestamp": file_mtime,
                            "metadata": data.get("metadata", {}),
                            "summary": data.get("summary", {}),
                            "top_evidence_count": len(tracks),
                            "tracks": tracks,
                            "evidence_tracks": tracks,
                            "status": data.get("status", "completed"),
                            "progress": data.get("progress", 100.0)
                        })
                except Exception:
                    pass

    # Sort descending by modification time (most recent first)
    history.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return history

@app.get("/api/stats")
def get_aggregate_stats():
    """Returns high-level surveillance KPI metrics."""
    history = get_analysis_history()
    total_videos = len(history)
    total_persons = sum(h.get("summary", {}).get("unique_persons_tracked", 0) for h in history)
    total_hq = sum(h.get("summary", {}).get("high_quality_evidence_count", 0) for h in history)
    
    qualities = [h.get("summary", {}).get("average_best_quality", 0) for h in history if h.get("summary", {}).get("average_best_quality", 0) > 0]
    avg_quality = round(sum(qualities) / len(qualities), 1) if qualities else 0.0

    return {
        "total_videos_analyzed": total_videos,
        "total_persons_tracked": total_persons,
        "high_quality_evidence_captured": total_hq,
        "system_average_fidelity": avg_quality,
        "active_models": ["YOLOv8-Tracking", "Cascade-Biometrics", "Laplacian-Fidelity-v2"]
    }

@app.get("/api/evaluation/latest")
def get_latest_evaluation():
    """Returns the latest measured benchmark metrics and forensic model report."""
    report_path = os.path.join(BASE_DIR, "evaluation", "latest_evaluation_report.json")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="No evaluation report has been generated yet.")
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read evaluation report: {str(e)}")

@app.post("/api/evaluation/run")
async def run_evaluation():
    """Executes a full evaluation run across the dataset manifest and updates the latest report."""
    from evaluation.generate_report import generate_full_evaluation_report
    loop = asyncio.get_event_loop()
    try:
        report = await loop.run_in_executor(executor, generate_full_evaluation_report)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation run failed: {str(e)}")


# ==========================================
# Live Camera Vision Pipeline & Endpoints
# ==========================================
_CAMERA_PERSON_DETECTOR: Optional[PersonDetector] = None
_CAMERA_FACE_DETECTOR: Optional[FaceDetector] = None

def get_camera_detectors():
    global _CAMERA_PERSON_DETECTOR, _CAMERA_FACE_DETECTOR
    if _CAMERA_PERSON_DETECTOR is None:
        _CAMERA_PERSON_DETECTOR = PersonDetector(confidence_threshold=0.35)
    if _CAMERA_FACE_DETECTOR is None:
        _CAMERA_FACE_DETECTOR = FaceDetector(score_threshold=0.35)
    return _CAMERA_PERSON_DETECTOR, _CAMERA_FACE_DETECTOR

def sync_camera_detect(
    image_bytes: bytes,
    conf_thresh: float = 0.35,
    face_conf_thresh: float = 0.35
) -> Dict[str, Any]:
    """Processes a single live camera frame for person tracking and face detection."""
    t0 = time.time()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None or frame.size == 0:
        raise ValueError("Could not decode image frame. Please verify image payload.")

    h, w = frame.shape[:2]
    if h < 10 or w < 10:
        raise ValueError(f"Frame resolution ({w}x{h}) is too small.")

    p_det, f_det = get_camera_detectors()
    p_det.confidence_threshold = conf_thresh

    # 1. Detect and track people
    people = p_det.track(frame, persist=True)

    # 2. Detect faces with landmarks
    faces = f_det.detect_faces(frame, score_threshold=face_conf_thresh)

    # 3. Spatially associate faces with person tracks
    people, faces = FaceDetector.associate_faces_with_people(people, faces)

    elapsed_ms = round((time.time() - t0) * 1000, 1)

    return {
        "timestamp": round(time.time(), 3),
        "frame_width": w,
        "frame_height": h,
        "faces_detected": len(faces),
        "people_detected": len(people),
        "faces": faces,
        "people": people,
        "processing_time_ms": elapsed_ms,
        "detector_backend": "OpenCV YuNet (5-point facial landmarks)"
    }

@app.post("/api/camera/detect")
async def camera_detect(
    file: Optional[UploadFile] = File(None),
    frame: Optional[UploadFile] = File(None),
    conf_threshold: float = 0.35,
    face_conf_threshold: float = 0.35
):
    """
    Real-time live camera frame detection endpoint.
    Accepts raw compressed JPEG/PNG/WebP frame, extracts YOLO person tracks and deep face landmarks.
    """
    upload = file or frame
    if upload is None:
        raise HTTPException(status_code=400, detail="Missing image file. Submit multipart 'file' or 'frame'.")

    contents = await upload.read()
    if not contents or len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty frame payload received.")

    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Frame payload exceeds 15MB limit.")

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            executor,
            sync_camera_detect,
            contents,
            conf_threshold,
            face_conf_threshold
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[Camera Detect Error] {e}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.post("/api/camera/reset")
async def reset_camera_tracker():
    """Resets the live camera multi-object tracker."""
    p_det, _ = get_camera_detectors()
    p_det.reset_tracker()
    return {"status": "ok", "message": "Camera tracker state successfully reset"}

@app.get("/api/camera/status")
async def get_camera_status():
    """Returns camera vision engine status and model telemetry."""
    return {
        "status": "online",
        "service": "Kestral Live Camera Intelligence",
        "person_tracker": "YOLOv8 ByteTrack",
        "face_detector": "OpenCV YuNet Deep Neural Network",
        "landmarks": "5-point (eyes, nose, mouth corners)",
        "default_interval_ms": 600,
        "cuda_available": False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[BASE_DIR],
        reload_excludes=[
            "uploads/*",
            "uploads/**",
            "results/*",
            "results/**",
            "*.jpg",
            "*.png",
            "*.mp4",
            "*.json",
            "*.pt",
            "*.onnx",
            ".venv/*",
            ".venv/**"
        ],
        timeout_keep_alive=30
    )
