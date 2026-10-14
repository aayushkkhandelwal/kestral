import os
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ==============================================================================
# SECTION: AYUSH (Vision, Detector, GPU & Tracker Configuration)
# ==============================================================================
PERSON_MODEL_NAME = "yolov8n.pt"  # Can configure yolov8s.pt, yolov8m.pt, etc.
PERSON_IMGSZ = 640
PERSON_CONFIDENCE_THRESHOLD = 0.35
YUNET_SCORE_THRESHOLD = 0.45
YUNET_NMS_THRESHOLD = 0.30
FACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_detection_yunet.onnx")
SFACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_recognition_sface.onnx")

# Dynamic stride settings based on video duration
STRIDE_SHORT = 3    # < 400 frames
STRIDE_MEDIUM = 4   # 400 - 1200 frames
STRIDE_LONG = 5     # > 1200 frames

# Concurrency configuration
MAX_CONCURRENT_WORKERS = 3          # Maximum parallel video processing tasks
TARGET_WINDOW_DEFAULT_MARGIN_S = 60.0 # +-1 min transaction window default

# ==============================================================================
# SECTION: ANSHIKA (Quality v2, Best Frame, Runner-ups & Evaluation Config)
# ==============================================================================
# Composite Quality weights: Sharpness (0.30), Size (0.20), Pose (0.20), Exposure (0.15), Detector Confidence (0.15)
QUALITY_WEIGHT_SHARPNESS = 0.30
QUALITY_WEIGHT_SIZE = 0.20
QUALITY_WEIGHT_POSE = 0.20
QUALITY_WEIGHT_EXPOSURE = 0.15
QUALITY_WEIGHT_CONFIDENCE = 0.15

# Reference constants
SHARPNESS_REFERENCE = 300.0        # Reference Laplacian variance on normalized 112x112 crop
SIZE_REFERENCE_HEIGHT = 160.0       # Face height in pixels for 100% resolution score
MIN_FACE_HEIGHT_PIXELS = 18         # Below this, flag low_res and heavily penalize
MAX_RUNNER_UPS = 4                  # Number of alternate runner-up frames to keep
MIN_RUNNER_UP_INTERVAL_SEC = 0.5    # Minimum temporal separation between runner-up frames

# CLAHE & Deblurring Enhancers
CLAHE_LUMINANCE_THRESHOLD = 45.0    # Mean L-channel brightness threshold to trigger enhancement
CLAHE_CLIP_LIMIT = 2.5
CLAHE_TILE_GRID_SIZE = (8, 8)
DEBLUR_BLUR_THRESHOLD = 75.0        # Normalized sharpness below which deblur engine is triggered
DEBLUR_USM_AMOUNT = 1.4             # Adaptive unsharp masking weight
DEBLUR_USM_SIGMA = 1.2

# ==============================================================================
# SECTION: ADITI (Transactions, ROIs, Linking, Audit & Demo Auth)
# ==============================================================================
DATABASE_PATH = os.path.join(DATA_DIR, "kestral.db")
LINKING_TIME_PADDING_SEC = 1.5      # [start_s - pad, end_s + pad]
LINKING_CONFIDENCE_THRESHOLD = 0.60 # Confidence below which link is marked ambiguous
LINKING_CLOSE_MARGIN = 0.15         # Margin between #1 and #2 dwell below which marked ambiguous

# Demo Auth Users (Investigator & Admin roles)
DEMO_USERS: Dict[str, Dict[str, str]] = {
    "investigator": {
        "role": "investigator",
        "name": "Special Agent Roy",
        "badge": "INV-7049"
    },
    "admin": {
        "role": "admin",
        "name": "Director Sarah Connor",
        "badge": "ADM-001"
    }
}
DEFAULT_USER = "investigator"
