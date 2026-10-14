# Kestral 🦅
### AI-Powered Video Surveillance & Best-Frame Evidence Extraction

Kestral is an intelligent computer vision pipeline and analytics dashboard designed to process video streams, detect and track persons across frames using YOLOv8/v11 tracking algorithms, extract high-resolution faces, evaluate multi-dimensional visual quality metrics (sharpness, exposure, resolution, pose), and automatically isolate the single highest-fidelity **"Best Evidence Frame"** for every individual captured.

---

## 📁 Project Architecture

```
kestral/
├── backend/
│   ├── .venv/                      # Python virtual environment
│   ├── main.py                     # FastAPI application & REST endpoints
│   ├── services/
│   │   ├── video_processor.py      # Master video processing & pipeline coordinator
│   │   ├── person_detector.py      # YOLO person detection & object tracking
│   │   ├── face_detector.py        # Face detection within tracked subjects
│   │   ├── face_quality.py         # Multi-metric quality assessment (blur, light, resolution)
│   │   └── best_frame.py           # Per-track optimal evidence selection & cropping
│   ├── models/                     # Model weights & cascade definitions
│   ├── uploads/                    # Staged video uploads
│   ├── results/                    # Processed evidence frames & metadata JSONs
│   └── requirements.txt            # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx         # Navigation & platform status
│   │   │   ├── StatsCards.jsx      # Dynamic KPI metrics cards
│   │   │   ├── VideoUploader.jsx   # Drag-and-drop video upload component
│   │   │   ├── TrackResults.jsx    # Real-time / completed track listing
│   │   │   └── EvidenceViewer.jsx  # Detailed evidence modal & quality inspector
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Overview, system health, and recent feeds
│   │   │   ├── Analysis.jsx        # Live video processing & tracking playback
│   │   │   └── Evidence.jsx        # Searchable, filterable evidence gallery
│   │   ├── App.jsx                 # Main application layout & state
│   │   ├── main.jsx                # React DOM entrypoint
│   │   └── index.css               # Modern dark-mode styling system
│   └── package.json
│
├── README.md
└── .gitignore
```

---

## ⚡ Quick Start

### 1. Backend Setup

Ensure Python 3.10+ is installed:

```bash
cd backend
# Activate your virtual environment:
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install requirements (if not already installed):
pip install -r requirements.txt

# Start the FastAPI server:
uvicorn main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Frontend interface will be running at `http://localhost:5173`.

---

## 🚀 Key Features

- **Person Detection & Tracking**: Persistent tracking across video frames using YOLO multi-object tracking.
- **Intelligent Face Extraction**: Automatic localized facial detection within detected person bounding boxes.
- **Multi-Factor Quality Scorer**: Computes Laplacian sharpness variance, exposure balance, pixel density, and symmetry scores.
- **Automated Evidence Selection**: Automatically ranks and isolates the crispest, most identifiable frame for every person.
- **Interactive Evidence Vault**: Filter by score, confidence, or timestamp, and export evidence packages.
