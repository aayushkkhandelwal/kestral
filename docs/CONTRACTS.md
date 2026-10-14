# CONTRACTS (ADDITIVE ONLY). Existing names/types never change: the React app depends on them.
Timestamps: float seconds from video start. Boxes `[x1,y1,x2,y2]` in ORIGINAL frame pixels. Scores 0..100 unless stated. Base URL `http://<host>:8000`.

## A. Existing (as in the code today)
Endpoints: `GET /api/health`, `POST /api/upload-and-process` (multipart `file`) -> `{task_id, filename, status, message}`, `GET /api/tasks/{id}/status`, `GET /api/tasks/{id}/results`, `GET /api/history`, `GET /api/stats`, `POST /api/camera/detect|reset`, `GET /api/camera/status`. Static: `/results/<task_id>/...`, `/uploads/...`.

results.json:
```json
{"task_id":"ab12cd34","status":"completed","progress":100.0,
 "metadata":{"total_frames":0,"fps":25.0,"resolution":"1280x720","duration_seconds":0.0,"frames_processed":0,"elapsed_time_sec":0.0},
 "summary":{"unique_persons_tracked":0,"total_detections":0,"average_best_quality":0.0,"high_quality_evidence_count":0},
 "tracks":[{"track_id":1,"first_seen_time":0.0,"last_seen_time":0.0,"duration_seconds":0.0,"total_detections":0,
   "best_frame_idx":0,"best_timestamp":0.0,"best_score":0.0,"has_real_face":true,"average_score":0.0,
   "quality":{"overall_score":0.0,"grade":"GOOD","has_real_face":true,"sharpness":0.0,"sharpness_normalized":0.0,"resolution_score":0.0,"brightness":0.0,"brightness_score":0.0,"contrast":0.0,"contrast_score":0.0,"crop_width":0,"crop_height":0},
   "person_bbox":[0,0,0,0],"face_bbox":[0,0,0,0],
   "face_image_url":"/results/<task_id>/track_1_face.jpg","full_frame_url":"/results/<task_id>/track_1_full.jpg"}]}
```

## B. Additions (adding task in brackets). Consumers treat all as OPTIONAL until that task is merged.
- `metadata.thumbnail_url` string: first-frame image, used to draw the ATM zone [T0.8, Ayush]
- `tracks[].trajectory`: `[[t, x1, y1, x2, y2], ...]` person box per processed frame [T0.8, Ayush]
- `tracks[].quality` extra keys [T2, Anshika]: `size_score`, `pose_score`, `yaw_proxy`, `pitch_proxy`, `exposure_score`, `enhanced` (bool, CLAHE applied), `flags` (list of "low_res","dim","side_pose","blurry","no_face")
- `tracks[].runner_ups`: `[{"frame_idx":0,"timestamp":0.0,"score":0.0,"face_image_url":"..."}]`, up to 4 [T2, Anshika]
- `/api/health` real keys [T0.5, Ayush]: `cuda_available` (real), `person_model` (name), `face_model_loaded` (bool)
- `/api/stats`: with no data, numeric KPIs are `null` or 0, never fabricated [T0.4, Ayush]

## C. New endpoints
ATM zone [T3, Aditi]
- `PUT /api/rois/{atm_id}` body `{"polygon":[[x,y],...], "frame_width":1280, "frame_height":720}` -> same body. `GET /api/rois/{atm_id}`.

Transactions + linking [T3, Aditi]
- `POST /api/transactions` body `{"txn_id":"T001","atm_id":"ATM_A","task_id":"ab12cd34","start_s":12.0,"end_s":41.5}` -> transaction + LinkResult
- `GET /api/transactions?atm_id=&task_id=&ambiguous=` -> list. `GET /api/transactions/{txn_id}` -> one.
- `POST /api/transactions/{txn_id}/relink` -> recompute
- LinkResult: `{"txn_id":"T001","task_id":"ab12cd34","track_id":3,"confidence":0.0,"ambiguous":false,"candidates":[{"track_id":3,"dwell_s":0.0}]}`. `track_id` is null if nobody was in the zone.

Face search [T4, Ayush]
- `POST /api/search/face` multipart `file`, query `top_k=5` -> `[{"task_id":"","track_id":0,"similarity":0.0,"face_image_url":"","note":"similarity only; needs human review"}]`

Audit + demo login [T6, Aditi]
- Header `X-User: <username>` on all calls; demo users in `config.py` (roles `investigator`, `admin`). `GET /api/audit` (admin only) -> `[{"id":1,"ts":"ISO","user":"","role":"","action":"","detail":""}]`.
- This is DEMO-GRADE auth. Label it so in the UI and slides.

## D. Storage
Transactions, ROIs, audit log: SQLite `backend/data/kestral.db` (git-ignored). Embeddings: `backend/data/embeddings.npz` or a table (Ayush decides in T4 and logs it).

## E. Mocks for parallel work
In T0.6 Ayush and Aditi add stub routers that return contract-valid MOCK data, so Charvi can build every page immediately. Replace stubs task by task and remove them from the CONTEXT_LOG Mocks list.
