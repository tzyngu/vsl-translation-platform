from pathlib import Path
from typing import Iterator

import numpy as np


VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def iter_video_frames(video_path: str | Path) -> Iterator[np.ndarray]:
    """Yield BGR frames and always release the OpenCV video handle."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "opencv-python is required. Install dependencies with: pip install -r requirements.txt"
        ) from exc
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            yield frame
    finally:
        capture.release()
