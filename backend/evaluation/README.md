# Kestral AI — Evaluation Framework & Benchmark Suite

This directory contains the reproducible accuracy evaluation framework for **Kestral AI**, covering Person Detection, Multi-Object Tracking (MOT), YuNet Face Detection, Face Quality Scoring, and Forensic Evidence Integrity.

---

## 📁 Directory Structure

```
evaluation/
├── dataset_manifest.json          # Master manifest defining test scenarios, splits, and metadata
├── annotations/                   # Ground-truth bounding box and identity JSON annotations
│   ├── empty_scene_01.json
│   ├── crossing_paths.json
│   ├── disappear_reappear.json
│   └── low_light_blur.json
├── fixtures/                      # Standardized benchmark video sequences
├── metrics.py                     # Mathematical implementations for IoU, mAP@0.50, MOT, and SHA-256
├── evaluate_detection.py          # YOLOv8n detector benchmark script
├── evaluate_tracking.py           # ByteTrack tracking stability benchmark
├── evaluate_face_quality.py       # YuNet face detector & biometric quality evaluation
├── generate_report.py             # Orchestrator generating JSON and Markdown reports
└── README.md
```

---

## 📊 Benchmark Metrics Defined

### 1. Person & Face Detection
- **IoU (Intersection-over-Union)**: Bounding box overlap threshold (default: `0.50`).
- **One-to-One Matching**: Greedy Hungarian-style matching ensuring a single prediction maps to at most one ground-truth box.
- **Precision**: $\frac{\text{TP}}{\text{TP} + \text{FP}}$ (proportion of detections that are actual humans).
- **Recall**: $\frac{\text{TP}}{\text{TP} + \text{FN}}$ (proportion of actual humans successfully detected).
- **F1 Score**: Harmonic mean of Precision and Recall.
- **mAP@0.50**: Mean Average Precision computed by integrating the 11-point interpolated Precision-Recall curve across detection confidences.

### 2. Multi-Object Tracking (MOT)
- **ID Switches**: Count of occurrences where a tracked ground-truth subject changes their assigned predicted track ID.
- **Track Fragmentations**: Number of times an active track is interrupted for $>1$ frame and subsequently resumed.
- **Switch Rate**: Total ID switches divided by the number of ground truth identities.

### 3. Face Quality Scoring
- Evaluates the four standard components:
  - Sharpness (Laplacian variance, 40%)
  - Resolution (pixel density, 30%)
  - Luminance Balance (brightness deviation from 128, 15%)
  - Contrast (histogram standard deviation, 15%)
- Assesses edge case rejection on zero-sized, pure-black, and pure-white crops.

---

## 🛠️ How to Run Evaluations

Run the master evaluation generator:
```powershell
cd backend
.\.venv\Scripts\python.exe evaluation\generate_report.py
```
This produces:
- `backend/evaluation/latest_evaluation_report.json`
- `backend/evaluation/latest_evaluation_report.md`

To run individual evaluations:
```powershell
.\.venv\Scripts\python.exe evaluation\evaluate_detection.py
.\.venv\Scripts\python.exe evaluation\evaluate_tracking.py
.\.venv\Scripts\python.exe evaluation\evaluate_face_quality.py
```
