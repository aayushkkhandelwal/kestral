"""
Kestral AI Vision Services package.
"""

from .video_processor import VideoProcessor
from .person_detector import PersonDetector
from .face_detector import FaceDetector
from .face_quality import FaceQualityAssessor
from .best_frame import BestFrameSelector
from .identity_consolidator import IdentityConsolidator

__all__ = [
    "VideoProcessor",
    "PersonDetector",
    "FaceDetector",
    "FaceQualityAssessor",
    "BestFrameSelector",
    "IdentityConsolidator",
]
