# PROJECT BRIEF: Kestral for SKIT001

## 1. Problem statement (verbatim)
AI-Based Face Identification from ATM Footage. Develop an AI-based video analytics system capable of identifying and extracting the most relevant facial image of a person from ATM/CCTV footage recorded during a cash withdrawal transaction.
Expected solution should:
- Detect persons appearing in ATM footage.
- Identify the individual associated with a specific transaction.
- Select the clearest/highest-quality face frame.
- Perform face detection and image-quality assessment.
- Handle varying illumination, face angles, partial occlusion and low-resolution footage.
- Provide a searchable interface for authorized investigators.

## 2. Current state (from reading the code on 14 Oct 2026; NOT yet run by the assistant)
Backend (FastAPI, `backend/`):
- `main.py`: endpoints `/api/health`, `/api/upload-and-process`, `/api/tasks/{id}/status`, `/api/tasks/{id}/results`, `/api/history`, `/api/stats`, `/api/camera/detect|reset|status`. In-memory `TASKS`, results saved as `results/<task_id>/results.json`.
- `services/person_detector.py`: YOLOv8n (`yolov8n.pt`), `imgsz=480`, built-in ByteTrack via `model.track(persist=True)`.
- `services/face_detector.py`: OpenCV YuNet ONNX (`backend/models/face_detection_yunet.onnx`), 5 landmarks, falls back silently to a head crop with `has_real_face=False`.
- `services/face_quality.py`: sharpness (Laplacian var), resolution, brightness, contrast, score 0..100.
- `services/best_frame.py`: keeps ONE best frame per track.
- `services/video_processor.py`: frame stride 3/4/5, loop, progress, writes results.json.
Frontend (React 19 + Vite, `frontend/`): Dashboard, Analysis, Evidence, LiveCamera pages, axios to `http://<host>:8000`.

## 3. Known issues (to fix first; all unverified until run)
1. Model files are git-ignored and not in the repo, no download step => face detection silently disabled on fresh clones.
2. `process_video` never resets the shared tracker; singleton detector shared across uploads => leaked IDs, corrupted tracks on concurrent uploads.
3. `/api/stats` returns fake `78.4` when empty; `cuda_available` hard-coded `False`; model labels ("Cascade-Biometrics") do not match what runs.
4. `yolov8n` at `imgsz=480`: weak for small faces; GPU not used/reported.
5. Quality: no pose term (README claims symmetry), sharpness not size-normalized, no low-light handling, no runner-up frames.
6. No per-track trajectory stored (needed for linking), no thumbnail frame (needed to draw the ATM zone).

## 4. Gaps vs problem statement
| Requirement | Status | Task |
|---|---|---|
| Detect persons | Works, weak model | T1 |
| Person linked to a transaction | MISSING | T3 |
| Best face frame | Partial | T2 |
| Quality + robustness (light, angle, occlusion, low-res) | Weak | T2 |
| Searchable interface for investigators | Partial (no face search, audit, login) | T4, T6, U-tasks |

## 5. Scope
MUST: T0 fixes, linking (T3), quality v2 (T2), UI for transactions + evidence (U2, U3), evaluation table (T5).
SHOULD: face search (T4), audit log + demo login (T6), detector upgrade (T1).
COULD: super-resolution on the displayed crop, learned face-quality model, RF-DETR swap.
WON'T: real-world identity databases, live multi-camera streaming.

## 6. Target architecture
```
upload video (+ transaction record, ATM zone)
  -> person detect + track (YOLO, GPU)  -> face detect (YuNet) + landmarks
  -> quality v2 (sharpness, size, pose, exposure, conf) + CLAHE for dark frames
  -> best frame + 4 runner-ups per track, trajectory saved
  -> linking: track with most dwell in ATM zone during transaction window
  -> embeddings (face search)  -> results.json + small SQLite for transactions/audit
  -> React UI: transactions, evidence view, face search, audit
```

## 7. Demo script (3 min)
1. Upload an ATM clip, add its transaction. 2. Show linked person, best face, quality bars, runner-ups. 3. Show a dark/side-angle/mask case. 4. Upload a face photo, search other transactions. 5. Show audit log, privacy design, honest limits.
