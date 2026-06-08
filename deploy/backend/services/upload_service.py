import asyncio
from pathlib import Path

import numpy as np
from django.db.models import F
from fastapi import UploadFile

from core.models import Gesture, UploadedSample
from src.preprocessing.mediapipe_extractor import extract_keypoints_from_video
from src.preprocessing.normalization import normalize_hand_keypoints
from src.preprocessing.sequence_sampling import uniform_sample_sequence

from ..config import get_settings
from ..utils import safe_filename


settings = get_settings()
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


async def save_and_process_upload(user_id: int, gesture_id, upload: UploadFile) -> UploadedSample:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        raise ValueError(f"Unsupported video extension: {suffix}")
    content = await upload.read()
    return await asyncio.to_thread(
        _save_and_process_upload, user_id, gesture_id, upload.filename or "video.mp4", content
    )


def _save_and_process_upload(user_id: int, gesture_id, filename: str, content: bytes) -> UploadedSample:
    sample = UploadedSample(user_id=user_id, gesture_id=gesture_id, keypoint_path="", status="processing")
    upload_dir = settings.media_path / "uploads" / str(user_id) / str(gesture_id)
    keypoint_dir = settings.media_path / "keypoints" / str(user_id) / str(gesture_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    keypoint_dir.mkdir(parents=True, exist_ok=True)
    video_path = upload_dir / f"{sample.id}_{safe_filename(filename)}"
    video_path.write_bytes(content)

    sequence, original_frames, valid_frames = extract_keypoints_from_video(
        video_path, model_path=settings.project_path(settings.hand_landmarker_path)
    )
    if valid_frames == 0:
        raise ValueError("No hand keypoints detected")
    if valid_frames < 5:
        raise ValueError(f"Only {valid_frames} valid keypoint frames; at least 5 are required")
    processed = uniform_sample_sequence(normalize_hand_keypoints(sequence), 30)
    keypoint_path = keypoint_dir / f"{sample.id}.npy"
    np.save(keypoint_path, processed.astype(np.float32))

    sample.video_path = str(video_path)
    sample.keypoint_path = str(keypoint_path)
    sample.status = "processed"
    sample.num_original_frames = original_frames
    sample.num_valid_frames = valid_frames
    sample.save()
    Gesture.objects.filter(pk=gesture_id, owner_id=user_id).update(num_samples=F("num_samples") + 1)
    return sample
