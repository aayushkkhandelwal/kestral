"""
Kestral AI - AI Pipeline Adapters package.
"""

from .adapters import (
    VisionPipelineAdapter,
    VideoProcessor,
    PersonDetector,
    FaceDetector,
    FaceQualityAssessor,
    BestFrameSelector,
    IdentityConsolidator,
)

__all__ = [
    "VisionPipelineAdapter",
    "VideoProcessor",
    "PersonDetector",
    "FaceDetector",
    "FaceQualityAssessor",
    "BestFrameSelector",
    "IdentityConsolidator",
]
