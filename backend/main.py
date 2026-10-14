import os
import uuid
import json
import shutil
import asyncio
import time
import threading
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import config
import db
from services.video_processor import VideoProcessor
from services.person_detector import PersonDetector
from services.face_detector import FaceDetector

# Import modular feature routers (T0.6)
from routers.rois import router as rois_router
from routers.transactions import router as transactions_router
from routers.search import router as search_router
from routers.audit import router as audit_router

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

app = FastAPI(
    title="Kestral Video Intelligence & Best-Frame Evidence API",
    description="Automated Person Tracking, Face Detection, and Biometric Evidence Extraction",
    version="1.0.0"
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
app.mount("/results", StaticFiles(directory=config.RESULTS_DIR), name="results")
app.mount("/uploads", StaticFiles(directory=config.UPLOADS_DIR), name="uploads")

# Include modular feature routers
app.include_router(rois_router)
app.include_router(transactions_router)
app.include_router(search_router)
app.include_router(audit_router)

# Execution lock: process one video upload at a time to prevent tracker ID collisions (T0.3)
_VIDEO_PROCESSING_LOCK = threading.Lock()
executor = ThreadPoolExecutor(max_workers=2)

# In-memory task registry
TASKS: Dict[str, Dict[str, Any]] = {}

def sync_process_video_wrapper(task_id: str, video_path: str, output_dir: str):
    """Worker function executed with single-processor concurrency guard."""
    def on_progress(p: Dict[str, Any]):
        if task_id in TASKS:
            TASKS[task_id].update(p)

    with _VIDEO_PROCESSING_LOCK:
        try:
            processor = VideoProcessor(confidence_threshold=config.PERSON_CONFIDENCE_THRESHOLD)
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
            db.log_audit(
                username="system",
                role="service",
                action="PROCESS_VIDEO",
                detail=f"Completed video processing for task {task_id}: {len(results.get('tracks', []))} tracks identified"
            )
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
    """
    Returns real hardware telemetry, loaded model identifiers, and status (T0.5).
    """
    cuda_avail = bool(torch.cuda.is_available()) if HAS_TORCH else False
    face_det = FaceDetector()

    return {
        "status": "online",
        "service": "Kestral Evidence Engine",
        "version": "1.0.0",
        "cuda_available": cuda_avail,
        "person_model": config.PERSON_MODEL_NAME,
        "face_model_loaded": face_det.face_model_loaded,
        "face_recognizer_loaded": face_det.face_recognizer_loaded
    }

@app.post("/api/upload-and-process")
async def upload_and_process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_user: str = Header(default="investigator")
):
    """
    Receives an uploaded video, initiates YOLO tracking & best-frame extraction in background.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")

    task_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    saved_filename = f"{task_id}_{file.filename}"
    video_path = os.path.join(config.UPLOADS_DIR, saved_filename)
    output_dir = os.path.join(config.RESULTS_DIR, task_id)

    # Save uploaded file chunk by chunk
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    TASKS[task_id] = {
        "task_id": task_id,
        "filename": file.filename,
        "video_url": f"/uploads/{saved_filename}",
        "status": "queued",
        "progress": 0.0,
        "tracks_count": 0,
        "current_frame": 0,
        "total_frames": 0,
        "processing_fps": 0.0
    }

    db.log_audit(
        username=x_user,
        role="investigator",
        action="UPLOAD_VIDEO",
        detail=f"Uploaded {file.filename} (task: {task_id})"
    )

    # Dispatch to background thread pool
    background_tasks.add_task(
        sync_process_video_wrapper,
        task_id=task_id,
        video_path=video_path,
        output_dir=output_dir
    )

    return {
        "task_id": task_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Video queued for analysis"
    }

@app.get("/api/tasks/{task_id}/status")
def get_task_status(task_id: str):
    """Returns real-time progress of a video analysis task."""
    if task_id not in TASKS:
        saved_json = os.path.join(config.RESULTS_DIR, task_id, "results.json")
        if os.path.exists(saved_json):
            with open(saved_json, "r") as f:
                data = json.load(f)
            return {
                "task_id": task_id,
                "status": "completed",
                "progress": 100.0,
                "result": data
            }
        raise HTTPException(status_code=404, detail="Task not found")

    return TASKS[task_id]

@app.get("/api/tasks/{task_id}/results")
def get_task_results(task_id: str):
    """Fetches detailed evidence tracks and metadata for a completed task."""
    saved_json = os.path.join(config.RESULTS_DIR, task_id, "results.json")
    if os.path.exists(saved_json):
        with open(saved_json, "r") as f:
            return json.load(f)

    if task_id in TASKS and TASKS[task_id].get("status") == "completed":
        return TASKS[task_id].get("result")

    if task_id in TASKS:
        return {"status": TASKS[task_id]["status"], "progress": TASKS[task_id]["progress"]}

    raise HTTPException(status_code=404, detail="Task result not found")

@app.get("/api/history")
def get_analysis_history():
    """Lists all historical analyses and summaries saved in the results directory."""
    history = []
    if not os.path.exists(config.RESULTS_DIR):
        return history

    for folder_name in os.listdir(config.RESULTS_DIR):
        task_dir = os.path.join(config.RESULTS_DIR, folder_name)
        if os.path.isdir(task_dir):
            json_file = os.path.join(task_dir, "results.json")
            if os.path.exists(json_file):
                try:
                    with open(json_file, "r") as f:
                        data = json.load(f)
                        history.append({
                            "task_id": data.get("task_id", folder_name),
                            "metadata": data.get("metadata", {}),
                            "summary": data.get("summary", {}),
                            "top_evidence_count": len(data.get("tracks", []))
                        })
                except Exception:
                    pass

    return history

@app.get("/api/stats")
def get_aggregate_stats():
    """
    Returns high-level surveillance KPI metrics.
    With no data, numeric KPIs are null or 0, never fabricated (T0.4).
    """
    history = get_analysis_history()
    total_videos = len(history)
    total_persons = sum(h.get("summary", {}).get("unique_persons_tracked", 0) for h in history)
    total_hq = sum(h.get("summary", {}).get("high_quality_evidence_count", 0) for h in history)

    qualities = [
        h.get("summary", {}).get("average_best_quality", 0)
        for h in history
        if h.get("summary", {}).get("average_best_quality", 0) > 0
    ]
    avg_quality = round(sum(qualities) / len(qualities), 1) if qualities else None

    return {
        "total_videos_analyzed": total_videos,
        "total_persons_tracked": total_persons,
        "high_quality_evidence_captured": total_hq,
        "system_average_fidelity": avg_quality,
        "active_models": [
            f"YOLOv8-Tracking ({config.PERSON_MODEL_NAME})",
            "OpenCV-YuNet-DNN",
            "SFace-Feature-128D",
            "Quality-v2-Laplacian"
        ]
    }

# ==========================================
# Live Camera Vision Pipeline & Endpoints
# ==========================================
_CAMERA_PERSON_DETECTOR: Optional[PersonDetector] = None
_CAMERA_FACE_DETECTOR: Optional[FaceDetector] = None

def get_camera_detectors():
    global _CAMERA_PERSON_DETECTOR, _CAMERA_FACE_DETECTOR
    if _CAMERA_PERSON_DETECTOR is None:
        _CAMERA_PERSON_DETECTOR = PersonDetector(confidence_threshold=config.PERSON_CONFIDENCE_THRESHOLD)
    if _CAMERA_FACE_DETECTOR is None:
        _CAMERA_FACE_DETECTOR = FaceDetector(score_threshold=config.YUNET_SCORE_THRESHOLD)
    return _CAMERA_PERSON_DETECTOR, _CAMERA_FACE_DETECTOR

def sync_camera_detect(
    image_bytes: bytes,
    conf_thresh: float = 0.35,
    face_conf_thresh: float = 0.35
) -> Dict[str, Any]:
    t0 = time.time()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None or frame.size == 0:
        raise ValueError("Could not decode image frame.")

    h, w = frame.shape[:2]
    if h < 10 or w < 10:
        raise ValueError(f"Frame resolution ({w}x{h}) is too small.")

    p_det, f_det = get_camera_detectors()
    p_det.confidence_threshold = conf_thresh
    f_det.score_threshold = face_conf_thresh

    people = p_det.track(frame, persist=True)

    # Detect faces in upper bodies
    detected_faces = []
    for person in people:
        face_info = f_det.detect_face_in_person(frame, person["bbox"])
        if face_info and face_info.get("has_real_face"):
            detected_faces.append({
                "bbox": face_info["bbox"],
                "confidence": face_info.get("confidence", 0.0),
                "matched_track_id": person["track_id"],
                "landmarks": face_info.get("landmarks", [])
            })
            person["face_bbox"] = face_info["bbox"]
            person["face_confidence"] = face_info.get("confidence", 0.0)
            person["has_real_face"] = True
        else:
            person["face_bbox"] = None
            person["face_confidence"] = None
            person["has_real_face"] = False

    t_diff = time.time() - t0
    inf_fps = round(1.0 / max(0.001, t_diff), 1)

    return {
        "status": "success",
        "timestamp": round(time.time(), 3),
        "frame_width": w,
        "frame_height": h,
        "frame_dimensions": [w, h],
        "faces_detected": len(detected_faces),
        "people_detected": len(people),
        "persons_detected": len(people),
        "faces": detected_faces,
        "people": people,
        "processing_time_ms": round(t_diff * 1000, 1),
        "inference_time_ms": round(t_diff * 1000, 1),
        "inference_fps": inf_fps,
        "detector_backend": "OpenCV YuNet (5-point facial landmarks)"
    }

@app.post("/api/camera/detect")
async def camera_detect(
    file: Optional[UploadFile] = File(None),
    frame: Optional[UploadFile] = File(None),
    conf_thresh: float = 0.35,
    face_conf_thresh: float = 0.35,
    conf_threshold: Optional[float] = None,
    face_conf_threshold: Optional[float] = None
):
    upload = file or frame
    if upload is None:
        raise HTTPException(status_code=400, detail="Missing image file. Submit multipart 'file' or 'frame'.")
    effective_conf = conf_threshold if conf_threshold is not None else conf_thresh
    effective_face_conf = face_conf_threshold if face_conf_threshold is not None else face_conf_thresh
    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty frame uploaded.")
    try:
        res = await asyncio.get_event_loop().run_in_executor(
            executor,
            sync_camera_detect,
            contents,
            effective_conf,
            effective_face_conf
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/camera/reset")
async def reset_camera_tracker():
    """Resets the live camera multi-object tracker."""
    p_det, _ = get_camera_detectors()
    p_det.reset_tracker()
    return {"status": "ok", "message": "Camera tracker state successfully reset"}

@app.get("/api/camera/status")
async def get_camera_status():
    """Returns camera vision engine status and model telemetry."""
    p_det, f_det = get_camera_detectors()
    return {
        "status": "online",
        "service": "Kestral Live Camera Intelligence",
        "person_tracker": "YOLOv8 ByteTrack",
        "face_detector": "OpenCV YuNet Deep Neural Network",
        "landmarks": "5-point (eyes, nose, mouth corners)",
        "default_interval_ms": 600,
        "cuda_available": bool(torch.cuda.is_available()) if HAS_TORCH else False,
        "person_detector_ready": p_det.model is not None,
        "face_detector_ready": f_det.face_model_loaded,
        "face_recognizer_ready": f_det.face_recognizer_loaded,
        "device": p_det.device
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

