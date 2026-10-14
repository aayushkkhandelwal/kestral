# TASKS (owners PROPOSED; change in CONTEXT_LOG)
Priority: MUST / SHOULD / COULD. "Done when" is checked by RUNNING, not by the AI saying so.
If time is short: do T0, T3, T2, U1 to U3, T5, then demo. Cut T1 extras, T4, T6 in that order.

## Ownership
Ayush: vision files + search. Anshika: quality/best-frame/eval + merges. Aditi: transactions/ROI/linking/audit. Charvi: `frontend/**`. Details in GIT_WORKFLOW.md.

## T0: Fix the basics (MUST, do first, ~1h). Merge before others start T1 to T4
| ID | Owner | Task | Done when |
|---|---|---|---|
| T0.1 | Anshika | Put AGENTS.md at repo root and the rest in `docs/`; merge `docs/guardrails` | All 4 can pull them |
| T0.2 | Ayush | `backend/scripts/download_models.py` fetches the YuNet ONNX from its official source (verify the source and license) into `backend/models/`; README step added | Fresh clone + script => face model present |
| T0.2b | Ayush | `FaceDetector` raises a clear error (or health shows `face_model_loaded:false`) if the model is missing. No silent head-crop fallback hiding it | Delete model, start server, see the error |
| T0.3 | Ayush | `reset_tracker()` at the start of `process_video`; one video processed at a time (lock/queue) | Upload the same video twice: track IDs start fresh |
| T0.4 | Ayush | `/api/stats`: remove fake `78.4`; labels reflect real models | Empty system returns null/0 |
| T0.5 | Ayush | Real `cuda_available` via torch; pass the device to YOLO; add `person_model`, `face_model_loaded` to `/api/health` | Shows true on the GPU machine |
| T0.6 | Ayush + Aditi | Create `backend/routers/`, `backend/config.py` (sections per owner), include routers in `main.py` (one line each); stub MOCK routes for transactions, rois, search, audit per CONTRACTS | `/docs` lists the new routes returning mock data |
| T0.7 | Ayush | Pin `requirements.txt` to installed versions; note the CUDA torch install step in README | Clean venv install works |
| T0.8 | Ayush | Save `metadata.thumbnail_url` (first frame) and `tracks[].trajectory` in results.json | New results.json has both |

## T1: Vision upgrade (SHOULD, Ayush)
- T1.1 Make model name, `imgsz`, stride, confidence configurable in `config.py`. Try a larger YOLO and `imgsz` 960 on the GPU. Benchmark fps and detections on 3 clips; log numbers in CONTEXT_LOG.
- T1.2 Face detection on the upper-body crop, upscaled when small; verify faces are found more often than before (count on the same clips).
- T1.3 (COULD) Try YOLO26 or RF-DETR if the installed Ultralytics supports it; keep only if clearly better on our clips.
Done when: before/after table (faces found, fps) exists with measured numbers.

## T2: Quality v2 + best frame (MUST, Anshika)
- T2.1 Size-normalized sharpness (resize crop before Laplacian), exposure, size score; weights in `config.py`.
- T2.2 Pose proxy from the 5 landmarks (see TECH_NOTES), `pose_score`, flag `side_pose`.
- T2.3 CLAHE on dark crops (`enhanced` flag); retry face detection on the enhanced frame if none found.
- T2.4 Keep the top 5 frames per track (runner-ups at least 0.5 s apart), light temporal smoothing.
- T2.5 Add the new fields from CONTRACTS section B. Do not rename existing keys.
- T2.6 Tests: `backend/tests/test_quality.py` prints sub-scores for sharp/blurry/dark/side crops and checks the ordering.
Done when: on 3 clips, the chosen frame is visibly better than the old one, and the UI still loads.

## T3: Transactions + linking (MUST, Aditi)
- T3.1 SQLite `db.py` (transactions, rois). ROI endpoints per CONTRACTS.
- T3.2 `services/linking.py`: for each track use `trajectory`, bottom-center point of the person box inside the ROI polygon, dwell within `[start_s - pad, end_s + pad]`, confidence = best dwell / total dwell, `ambiguous` if confidence below a threshold or top two close.
- T3.3 Transaction endpoints and relink per CONTRACTS.
- T3.4 Tests with synthetic trajectories: one person, two queued people, person passing behind, nobody in zone.
Done when: test cases pass and a real processed video links the right track.

## T4: Face search (SHOULD, Ayush)
- T4.1 Pick the embedding method (SFace through OpenCV vs InsightFace; see TECH_NOTES), log the decision.
- T4.2 Compute an embedding for each best face; store; `POST /api/search/face`; cosine similarity in NumPy.
- T4.3 Label results as similarity only.
Done when: searching with a crop of a known person returns their other appearances in the top results on our test clips (report the measured hit rate).

## T5: Evaluation + data (MUST, Anshika; Aditi helps record)
- T5.1 Record at least 6 consented mock ATM clips: clean, dim, side-angle, mask/cap, low-res, two-person queue. Write the transactions for them.
- T5.2 `eval/` script: link accuracy, best-frame hit rate (human picks the top 3 frames per person), face detection rate per condition, fps.
- T5.3 Results table for the slides. Report only measured numbers and list the failures.

## T6: Audit + demo login (SHOULD, Aditi)
Audit table and `X-User` check, `GET /api/audit` (admin). Charvi builds the login and audit pages (U5).

## Frontend tasks (Charvi). Build against mocks; wire to real endpoints as backends merge
- U1 Handle null/missing stats and the new `health` keys; show "no data" instead of numbers. (MUST)
- U2 Transactions page: add transaction form (pick processed task, ATM, start/end), list with link status and "ambiguous" badge, ROI drawing over `thumbnail_url` (click polygon, save). (MUST)
- U3 Evidence view: quality breakdown bars (all sub-scores), flags as chips, runner-ups strip, trajectory/dwell info for the linked transaction, short note when ambiguous. (MUST)
- U4 Face search page: upload image, show top-k with similarity and the "needs human review" note. (SHOULD)
- U5 Login (demo users) + audit page (admin). (SHOULD)
- U6 Polish: empty/loading/error states, layout on a projector, a README screenshot. (COULD)
Rule: any field you need that is not in CONTRACTS goes to CONTEXT_LOG "REQUESTS". Do not invent fields.

## T7: Integration, demo, pitch (all)
- T7.1 End to end: upload, add transaction, linked evidence, search, audit. Fix mismatches.
- T7.2 Pre-process the demo videos and keep the results; record a backup demo video.
- T7.3 Slides: problem, pipeline, quality score, linking, robustness table, privacy and limits (non-commercial model licences, demo-grade auth), future work.
- T7.4 Rehearse twice. CODE FREEZE 3 hours before the deadline.
