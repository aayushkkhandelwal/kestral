# CONTEXT LOG (AI reads this every session; keep it short, newest first)

## Decisions
- D1: Frontend stays React/Vite (not Streamlit).
- D2: Person detector = YOLOv8n with configurable device (CUDA/MPS/CPU) and ByteTrack tracker reset.
- D3: Face detector = OpenCV YuNet ONNX. Face search = OpenCV SFace 128D cosine similarity.
- D4: Owners as proposed in docs/TASKS.md.
- D5: Quality v2 implemented with 112x112 normalized Laplacian, landmark pose proxy, exposure balance, and CLAHE enhancement.
- D6: SQLite database (`backend/data/kestral.db`) for ROIs, transactions, and investigator audit logs.
- D7: Top-4 runner-ups and spatial trajectory tracking saved in results.json and displayed in Evidence Dossier.

## Status
- Phase: T0 + T2 + T3 + T4 + T6 + U1-U5 complete and verified.

## Known issues (Resolved)
1. YuNet/SFace ONNX models now downloaded via `backend/scripts/download_models.py`.
2. Tracker reset added at start of video processing; processing lock prevents concurrent collision.
3. Fake 78.4 removed from `/api/stats`; returns `null`/0 when database is empty; telemetry in `/api/health` shows real models.
4. Quality v2 adds pose proxy, size-normalized sharpness, CLAHE low-light enhancement, and flags.
5. Trajectory and first-frame thumbnail now saved in results.json.

## Verified facts (library behaviour actually tested, with versions)
- opencv-python==5.0.0.93: `FaceDetectorYN_create` and `FaceRecognizerSF_create` verified with YuNet and SFace models.
- torch==2.14.1, ultralytics==8.4.177: YOLO person tracking + ByteTrack with `reset_tracker()` verified.
- `backend/tests/test_quality.py`: PASSED (sharp=96.8, blurry=65.1, dark=57.1 with CLAHE, side=77.5 with side_pose flag, non-face=9.2).
- `backend/tests/test_linking.py`: PASSED (single person 100% conf, passing behind ignored, queue flagged ambiguous, outside zone returns None).
- `backend/tests/test_api.py`: PASSED (health, stats, rois, transactions, audit, search all passed).
- Frontend: `npm run build` succeeded with zero errors.

## Mocks currently in the code (remove or label before the demo)
- (none - all routes wired to SQLite database and live models)

## REQUESTS (contract additions or cross-owner changes; AI must STOP and put them here)
- (none)

## Parking lot
- (none)

## Session log
### 2026-10-14 16:00 | Anshika | T0, T2, T3, T4, T6, U1-U5 | feat/anshika/core-evidence-pipeline
- Done:
  - T0: Downloaded official YuNet & SFace ONNX models, added ByteTrack resets, removed fake stats default, wired hardware telemetry in `/api/health`, and added concurrency lock.
  - T2: Built Quality v2 scoring engine (112x112 size-normalized Laplacian, pose proxy yaw/pitch, exposure balance, CLAHE enhancement, flags, top-4 runner-ups at least 0.5s apart).
  - T3: Built SQLite schema & CRUD (`backend/data/kestral.db`), ROI polygon zones, feet-dwell calculation with polygon tests, confidence scoring, and ambiguity detection.
  - T4: Implemented SFace 128D cosine similarity face search with mandatory "similarity only; needs human review" disclaimer.
  - T6: Implemented tamper-evident SQLite audit log with role-based identity switching (`investigator` vs `admin`).
  - U1-U5: Interactive frontend pages (Transactions + SVG ROI polygon editor, Face Search with dropzone & top-k, Audit Trail viewer, and EvidenceViewer with Quality v2 sub-scores and runner-ups strip).
- Files touched:
  - `AGENTS.md`, `docs/*`
  - `backend/config.py`, `backend/db.py`, `backend/main.py`, `backend/requirements.txt`, `.gitignore`
  - `backend/services/person_detector.py`, `face_detector.py`, `face_quality.py`, `best_frame.py`, `video_processor.py`, `linking.py`
  - `backend/routers/rois.py`, `transactions.py`, `search.py`, `audit.py`
  - `backend/scripts/download_models.py`
  - `backend/tests/test_quality.py`, `test_linking.py`, `test_api.py`
  - `frontend/src/App.jsx`, `components/Sidebar.jsx`, `components/StatsCards.jsx`, `components/EvidenceViewer.jsx`
  - `frontend/src/pages/Transactions.jsx`, `FaceSearch.jsx`, `AuditLog.jsx`
- Verified by running (command + result):
  - `backend/.venv/bin/pytest backend/tests/ backend/test_camera.py` -> 16 passed in 3.12s
  - `npm run build` -> built in 271ms with 0 errors
  - Browser subagent tour -> Dashboard, ATM Transactions + ROI canvas, Face Search, Audit Trail all rendered and functional
  - `curl http://127.0.0.1:8000/api/health` -> 200 OK with model status
- Not verified:
  - Physical ATM hardware camera feed (tested via synthetic frames and video processing test suite).
- Pushed:
  - Branch: `feat/anshika/core-evidence-pipeline`
  - Commit: `a2adf85`
  - PR URL: `https://github.com/aayushkkhandelwal/kestral/pull/new/feat/anshika/core-evidence-pipeline`
- Next:
  - Merge PR into `main` after team review.

