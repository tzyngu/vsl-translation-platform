from pathlib import Path

import numpy as np

from .video_reader import iter_video_frames


LANDMARKS_PER_HAND = 21
COORDINATES_PER_LANDMARK = 3
FEATURE_DIM = 2 * LANDMARKS_PER_HAND * COORDINATES_PER_LANDMARK
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "hand_landmarker.task"


def _landmarks_to_array(hand_landmarks) -> np.ndarray:
    landmarks = getattr(hand_landmarks, "landmark", hand_landmarks)
    return np.asarray(
        [[point.x, point.y, point.z] for point in landmarks],
        dtype=np.float32,
    )


def extract_keypoints_from_video(
    video_path: str | Path,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> tuple[np.ndarray, int, int]:
    """Extract [left hand, right hand] MediaPipe coordinates from every frame."""
    try:
        import cv2
        import mediapipe as mp
    except ImportError as exc:
        raise RuntimeError(
            "opencv-python and mediapipe are required. Install dependencies with: "
            "pip install -r requirements.txt"
        ) from exc

    if hasattr(mp, "solutions"):
        return _extract_with_legacy_solutions(
            video_path, cv2, mp, min_detection_confidence, min_tracking_confidence
        )
    return _extract_with_tasks(
        video_path, mp, model_path, min_detection_confidence, min_tracking_confidence
    )


def _extract_with_legacy_solutions(
    video_path, cv2, mp, min_detection_confidence, min_tracking_confidence
):
    frames: list[np.ndarray] = []
    num_valid_frames = 0
    with mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    ) as hands:
        for frame in iter_video_frames(video_path):
            feature = np.zeros((2, LANDMARKS_PER_HAND, COORDINATES_PER_LANDMARK), dtype=np.float32)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb_frame)
            if result.multi_hand_landmarks and result.multi_handedness:
                for landmarks, handedness in zip(
                    result.multi_hand_landmarks, result.multi_handedness
                ):
                    label = handedness.classification[0].label.lower()
                    hand_index = 0 if label == "left" else 1
                    feature[hand_index] = _landmarks_to_array(landmarks)
            if np.any(feature):
                num_valid_frames += 1
            frames.append(feature.reshape(FEATURE_DIM))

    sequence = np.asarray(frames, dtype=np.float32)
    if not frames:
        sequence = np.empty((0, FEATURE_DIM), dtype=np.float32)
    return sequence, len(frames), num_valid_frames


def _extract_with_tasks(
    video_path, mp, model_path, min_detection_confidence, min_tracking_confidence
):
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python import vision

    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"MediaPipe hand landmarker model is missing: {model_path}. "
            "Download models/hand_landmarker.task as described in README.md."
        )

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=min_detection_confidence,
        min_hand_presence_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )
    frames: list[np.ndarray] = []
    num_valid_frames = 0
    with vision.HandLandmarker.create_from_options(options) as landmarker:
        for timestamp_ms, frame in enumerate(iter_video_frames(video_path)):
            rgb_frame = frame[:, :, ::-1]
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = landmarker.detect_for_video(image, timestamp_ms)
            feature = np.zeros(
                (2, LANDMARKS_PER_HAND, COORDINATES_PER_LANDMARK), dtype=np.float32
            )
            for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
                label = handedness[0].category_name.lower()
                hand_index = 0 if label == "left" else 1
                feature[hand_index] = _landmarks_to_array(landmarks)
            if np.any(feature):
                num_valid_frames += 1
            frames.append(feature.reshape(FEATURE_DIM))

    sequence = np.asarray(frames, dtype=np.float32)
    if not frames:
        sequence = np.empty((0, FEATURE_DIM), dtype=np.float32)
    return sequence, len(frames), num_valid_frames
