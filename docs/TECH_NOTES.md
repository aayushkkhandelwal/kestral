# TECH NOTES (how-to for each stage). Verify every API against the INSTALLED version first (AGENTS.md section 2).

## 1. Detector (T1)
Today: `yolov8n.pt` at `imgsz=480`, tuned for CPU. On the GPU machine first try: a larger model size and `imgsz` 960, GPU device set explicitly (check the Ultralytics docs for the `device` argument). Options, in order of effort:
- A: bigger YOLO already supported by the installed Ultralytics (one-line change). Start here.
- B: YOLO26 (NMS-free, CPU-friendly, AGPL-3.0) if the installed version supports it.
- C: RF-DETR (Apache-2.0 for S/M/L) with `supervision` ByteTrack. More rework; only if A/B fail on our clips.
Person class only (COCO id 0). Tracking stays ByteTrack. Reset the tracker per video.

## 2. Face detection (T1.2)
Keep OpenCV YuNet (5 landmarks). Improve recall: search the upper ~40 to 60% of the person box, upscale small crops, keep the threshold in `config.py`. Alternative if YuNet is not enough: InsightFace SCRFD (also gives embeddings; pretrained models are non-commercial research only).

## 3. Quality v2 (T2)
Normalize each term to 0..1 then scale to 0..100. Starting weights (NOT validated, tune on our clips): sharpness 0.30, size 0.20, pose 0.20, exposure 0.15, detector conf 0.15. Gate out very small faces.
- Sharpness: resize the gray face crop to a fixed size (for example 112x112), then `cv2.Laplacian(...).var()`, divide by a reference constant from `config.py`.
- Size: face height in pixels over a reference height.
- Pose proxy (heuristic, check visually): with eye midpoint and inter-eye distance, `yaw_proxy = (nose_x - eye_mid_x) / inter_eye_dist`; large absolute value means side view. `pitch_proxy` from the nose's vertical position between the eye line and the mouth line. `pose_score = 1 - min(1, penalty)`.
- Exposure: distance of mean gray from mid-gray plus the fraction of clipped pixels.
- Low light: LAB color space, `cv2.createCLAHE` on the L channel, only when mean luminance is below a threshold; set `enhanced=true`. Retry face detection on the enhanced frame if none found.
- Low resolution: just flag it (`low_res`). Super-resolution (GFPGAN/CodeFormer) only for the displayed crop, never for scoring/search.
- Optional learned quality model (CR-FIQA, SER-FIQ) after the MVP works; verify availability and licence.

## 4. Best frame + runner-ups (T2.4)
Per track keep a small list of (score, frame data). Smooth scores over 3 neighbours, choose the max, keep 4 runner-ups at least 0.5 s apart. Save crops and annotated frames like today (`track_<id>_face.jpg`; add `track_<id>_alt<k>.jpg`).

## 5. Linking (T3.2)
- Zone polygon in ORIGINAL frame pixels (the UI scales clicks using `frame_width/height`).
- Point = bottom-center of the person box (feet). Use `cv2.pointPolygonTest`.
- Dwell = in-zone samples x time step, restricted to `[start_s - pad, end_s + pad]`.
- Link to the max dwell; `confidence = best / sum`; flag `ambiguous` when confidence is below the threshold or the top two are close.
- Edge cases to test: queue of two, someone passing behind, person leaves before the transaction ends, nobody in zone.

## 6. Face search (T4)
- Option 1: OpenCV SFace (`FaceRecognizerSF`, pairs with YuNet, no new Python dependency, needs a separate ONNX file; verify API and licence). Lower accuracy.
- Option 2: InsightFace ArcFace (better, adds dependencies, non-commercial models).
- At our scale (hundreds of faces) NumPy cosine similarity is enough; no FAISS needed.
- Output is similarity, not identity. Show that in the UI.

## 7. Performance and demo
Process offline and cache results. GPU person processes all demo videos once and shares the `results/` folder content out of band (it is git-ignored), or everyone re-runs on their machine. Do not commit videos or results.

## 8. Common traps
Tracker ID leaks between videos; BGR vs RGB; coordinates after cropping or resizing; fps of 0 or variable; CORS/host (frontend uses the page hostname with port 8000); Windows paths; large `results/` growing the repo.
