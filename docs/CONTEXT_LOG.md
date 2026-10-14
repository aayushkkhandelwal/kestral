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
### 2026-10-14 15:45 | Anshika | T0, T2, T3, T4, T6, U1-U5 | main
- Done:
  - T0: Guardrail docs moved to root and `docs/`; model downloader `download_models.py` created; YuNet & SFace models fetched; tracker reset & concurrency lock added; real health telemetry & fake stats removed; requirements.txt pinned.
  - T2: Quality v2 assessor built with normalized Laplacian, landmark pose proxy, CLAHE low-light boost, flags, and runner-ups selection with temporal separation.
  - T3: SQLite database layer `db.py`, spatiotemporal linking engine `services/linking.py`, ROI polygon endpoints, and transaction endpoints.
  - T4: Biometric face search router `routers/search.py` using SFace cosine similarity.
  - T6: Tamper-evident audit trail `routers/audit.py` with demo role access.
  - U1-U5: Frontend pages created for Transactions (with interactive SVG ROI polygon drawer), Face Search, and Audit Trail; EvidenceViewer upgraded with Quality v2 sub-scores and runner-ups strip; Sidebar and StatsCards updated.
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
  - `backend/tests/test_quality.py` -> [PASS] All Quality v2 tests successfully verified!
  - `backend/tests/test_linking.py` -> [PASS] All transaction linking tests successfully verified!
  - `backend/tests/test_api.py` -> [ALL PASS] All FastAPI integration tests succeeded!
  - `npm run build` -> built in 303ms with 0 errors.
- Not verified:
  - Live ATM physical camera feed hardware (tested on synthetic frames and unit suites).
- Next:
  - Run dev servers and demonstrate full end-to-end pipeline.
