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
  - Implement mentoring feedback (multi-video, long footage, deblurring, multi-angle fusion, windowing, database search).

---

## 2026-10-14 23:05 IST — Anshika (Quality / Eval / Pipeline Integrator)
- Task: MENTORING-ALL — Implementation of all 6 Mentoring Feedback Points:
  1. Long duration video processing: Adaptive frame stride (stride 2..12 depending on length) and periodic memory collection.
  2. Multi-video concurrent processing: Concurrency semaphore (MAX_CONCURRENT_WORKERS=3), ThreadPoolExecutor, multi-video queue in UI.
  3. Image deblurring & sharpening: Dual-stage Unsharp Masking (USM) + bilateral edge-preserving smoothing restoring eyes and mouth contours.
  4. Multi-angle composite synthesis: Fused panoramic plate (`track_{id}_composite.jpg`) combining Profile A, Mertens detail-blended fused portrait, and Profile B with biometric markers.
  5. ATM location & timestamp capture + targeted transaction windowing: `atm_id`, `location_name`, `wall_clock_time`, plus ±1 min targeted temporal window seeking directly to `target_time_s - window_margin_s` and early termination to avoid processing hour-long clips.
  6. SQLite-backed face search: `evidence_faces` database table indexing all faces, 128D embeddings, locations, and timestamps with sub-millisecond search and database explorer registry.
- Changed files:
  - `backend/config.py`: Concurrency and deblurring hyperparameters.
  - `backend/db.py`: `evidence_faces` table, `save_evidence_face`, `get_all_evidence_faces`, `backfill_existing_results`.
  - `backend/services/face_quality.py`: `deblur_and_sharpen_image`, updated `enhance_crop_if_needed`.
  - `backend/services/best_frame.py`: Deblurred crop saving, `_generate_multi_angle_composite` panoramic plate generation.
  - `backend/services/video_processor.py`: Windowed seeking, adaptive stride, SQLite indexing.
  - `backend/main.py`: Concurrency semaphore, updated `/api/upload-and-process` with ATM targeting params.
  - `backend/routers/search.py`: Database-backed search and `/api/search/database-faces` endpoint.
  - `backend/tests/test_enhancements.py`: Comprehensive test suite for deblurring, fusion, db CRUD, and window math.
  - `frontend/src/components/VideoUploader.jsx`: Multi-video queue and Targeted Transaction Window / ATM location panel.
  - `frontend/src/pages/Analysis.jsx`: Multi-task concurrent progress monitor and tab switcher.
  - `frontend/src/components/EvidenceViewer.jsx`: AI Deblurred side-by-side mode and Multi-Angle Fused Identification Plate viewer.
  - `frontend/src/pages/FaceSearch.jsx`: SQLite database face search with location & timestamp badges, and Evidence Database registry tab.
- Verified by running:
  - `backend/.venv/bin/pytest backend/tests/ backend/test_camera.py` -> 20 passed in 2.97s (100% pass)
  - `npm run build` -> 0 errors, built in 307ms
  - Browser subagent tour -> Verified ±60s windowing preview, multi-video queue, database registry faces, AI deblurring comparison, and multi-angle composite card
- Pushed:
  - Branch: `feat/anshika/core-evidence-pipeline`

---

### 2026-10-15 03:30 IST — Anshika (Quality / Eval / Integrator)
- Task: T7.1, T7.2 — End-to-End Demo Walkthrough, Asset Recording & Pitch Preparation
- Done:
  - Restarted backend and frontend servers cleanly on ports 8000 and 5173.
  - Processed `f77b1b43_atm_video.mp4` via `/api/upload-and-process` using Targeted Windowing (task `d6045d17`, 10.0s +/- 10.0s window), verifying 150 frames processed in 8.46s (out of 7,433 total frames) with deblurred crop and composite plate generated.
  - Created and verified transaction `TXN-DEMO-01` linked with 100% confidence to Track #1.
  - Verified Face Search against indexed SQLite evidence database with sub-second response.
  - Recorded a full 4.8MB WebP browser walkthrough video capturing Dashboard, Analysis, Evidence Dossier (with Quality v2, AI Deblur side-by-side, composite plate, and runner-ups), Transactions ROI canvas, Face Search, and Audit Trail.
  - Generated comprehensive Hackathon Presentation Slide Deck guide and step-by-step Demo Script.
- Files touched:
  - `docs/CONTEXT_LOG.md`
- Verified by running:
  - `backend/.venv/bin/pytest backend/tests/ backend/test_camera.py` -> 20 passed (100% pass)
  - `curl http://127.0.0.1:8000/api/health` -> 200 OK (YuNet + SFace loaded)
  - Browser subagent demo recording -> `e2e_demo_walkthrough_1792011167255.webp` captured successfully
- Not verified:
  - Physical ATM hardware integration (tested with synthetic ATM CCTV sequences).
- Next:
  - Rehearse pitch with team and open/merge PR to `main`.



