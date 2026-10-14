"""
Kestral AI — 10-Second Pre/Post Event Video Buffer & Clip Slicing Service.
Extracts 10-second pre-event and 10-second post-event context around surveillance events,
generating forensic MP4 evidence clips with cryptographic SHA-256 integrity verification.
"""

import os
import cv2
import hashlib
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone


class ClipBufferService:
    """
    Automated pre/post event clipping engine.
    Extracts high-fidelity 20-second context clips centered on event timestamps.
    """

    def __init__(self, clips_dir: str = "clips"):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.clips_dir = os.path.join(backend_dir, clips_dir) if not os.path.isabs(clips_dir) else clips_dir
        os.makedirs(self.clips_dir, exist_ok=True)

    @staticmethod
    def calculate_sha256(filepath: str) -> str:
        """Computes cryptographic SHA-256 digest of a video file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest().lower()

    def extract_event_clip(
        self,
        video_path: str,
        event_timestamp_sec: float,
        event_id: str,
        pre_event_target_sec: float = 10.0,
        post_event_target_sec: float = 10.0
    ) -> Dict[str, Any]:
        """
        Slices a video around event_timestamp_sec:
        [event_timestamp_sec - pre_event_target_sec, event_timestamp_sec + post_event_target_sec].
        Handles start/end edge boundaries safely.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Source video not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_duration = total_frames / fps if fps > 0 else 0.0

        # Calculate exact time boundaries
        clip_start_sec = max(0.0, event_timestamp_sec - pre_event_target_sec)
        clip_end_sec = min(total_duration, event_timestamp_sec + post_event_target_sec)

        actual_pre_duration = round(event_timestamp_sec - clip_start_sec, 2)
        actual_post_duration = round(clip_end_sec - event_timestamp_sec, 2)

        start_frame = int(round(clip_start_sec * fps))
        end_frame = int(round(clip_end_sec * fps))

        # Output filename
        clip_filename = f"event_{event_id}.mp4"
        clip_abs_path = os.path.join(self.clips_dir, clip_filename)
        relative_url = f"/clips/{clip_filename}"

        # Initialize VideoWriter (mp4v codec)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(clip_abs_path, fourcc, fps, (width, height))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        curr_frame = start_frame

        frames_written = 0
        try:
            while curr_frame <= end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                frames_written += 1
                curr_frame += 1
        finally:
            cap.release()
            out.release()

        file_size = os.path.getsize(clip_abs_path) if os.path.exists(clip_abs_path) else 0
        sha256_hash = self.calculate_sha256(clip_abs_path) if file_size > 0 else None

        return {
            "clip_filename": clip_filename,
            "clip_path": relative_url,
            "clip_abs_path": clip_abs_path,
            "clip_start_sec": round(clip_start_sec, 2),
            "clip_end_sec": round(clip_end_sec, 2),
            "pre_event_duration": actual_pre_duration,
            "post_event_duration": actual_post_duration,
            "total_clip_duration": round(clip_end_sec - clip_start_sec, 2),
            "event_offset_in_clip_sec": actual_pre_duration,
            "frames_written": frames_written,
            "file_size_bytes": file_size,
            "sha256": sha256_hash,
            "fps": round(fps, 2),
            "resolution": f"{width}x{height}"
        }
