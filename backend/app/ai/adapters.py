"""
Kestral AI - Vision Pipeline Adapter.
Encapsulates existing YOLOv8 person tracking, OpenCV YuNet facial detection,
Laplacian quality scoring, and identity consolidation without rewriting their underlying AI logic.
"""

import os
import sys
from typing import Dict, Any, Callable, Optional, List, Tuple
import numpy as np

# Ensure both backend root and workspace root are on sys.path so services imports work reliably in any environment
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
workspace_root = os.path.dirname(backend_root)

for p in (backend_root, workspace_root):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.services.video_processor import VideoProcessor
    from backend.services.person_detector import PersonDetector
    from backend.services.face_detector import FaceDetector
    from backend.services.face_quality import FaceQualityAssessor
    from backend.services.best_frame import BestFrameSelector
    from backend.services.identity_consolidator import IdentityConsolidator
except ImportError:
    from services.video_processor import VideoProcessor  # type: ignore
    from services.person_detector import PersonDetector  # type: ignore
    from services.face_detector import FaceDetector  # type: ignore
    from services.face_quality import FaceQualityAssessor  # type: ignore
    from services.best_frame import BestFrameSelector  # type: ignore
    from services.identity_consolidator import IdentityConsolidator  # type: ignore


class VisionPipelineAdapter:
    """
    Adapter encapsulating existing YOLOv8 person tracking, OpenCV YuNet facial detection,
    and Laplacian quality scoring services without rewriting their underlying AI logic.
    """

    def __init__(self, confidence_threshold: float = 0.35):
        self.processor = VideoProcessor(confidence_threshold=confidence_threshold)
        self.person_detector = self.processor.person_detector
        self.face_detector = self.processor.face_detector
        self.quality_assessor = self.processor.quality_assessor
        self.identity_consolidator = IdentityConsolidator()

    def process_video_file(
        self,
        video_path: str,
        output_dir: str,
        task_id: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Runs the complete vision processing pipeline and returns structured extraction metadata."""
        return self.processor.process_video(
            video_path=video_path,
            output_dir=output_dir,
            task_id=task_id,
            progress_callback=progress_callback
        )

    def detect_persons(self, frame: np.ndarray, persist: bool = True) -> List[Dict[str, Any]]:
        """Processes a single frame for person tracking via YOLOv8 ByteTrack."""
        return self.person_detector.track(frame=frame, persist=persist)

    def detect_faces(self, frame: np.ndarray, score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Detects full-frame facial landmarks using OpenCV YuNet DNN."""
        if hasattr(self.face_detector, "detect_faces"):
            thresh = score_threshold if score_threshold is not None else self.face_detector.score_threshold
            return self.face_detector.detect_faces(frame, score_threshold=thresh)
        return []

    def detect_face_in_person(self, frame: np.ndarray, person_bbox: List[int]) -> Optional[Dict[str, Any]]:
        """Extracts and verifies face presence within a person bounding box."""
        return self.face_detector.detect_face_in_person(frame, person_bbox)

    def associate_faces_with_people(
        self, people: List[Dict[str, Any]], faces: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Spatially associates detected facial regions with tracked person bodies."""
        return FaceDetector.associate_faces_with_people(people, faces)

    def assess_face_quality(self, crop_img: np.ndarray, has_real_face: bool = True) -> Dict[str, Any]:
        """Calculates multi-dimensional biometric quality (sharpness, brightness, contrast, resolution)."""
        return FaceQualityAssessor.assess_crop(crop_img, has_real_face=has_real_face)

    def consolidate_identities(self, tracks: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """Consolidates fragmented identity tracks across temporal gaps."""
        return self.identity_consolidator.consolidate_tracks(tracks)


__all__ = [
    "VisionPipelineAdapter",
    "VideoProcessor",
    "PersonDetector",
    "FaceDetector",
    "FaceQualityAssessor",
    "BestFrameSelector",
    "IdentityConsolidator",
]
