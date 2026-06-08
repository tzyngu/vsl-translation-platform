import numpy as np


LANDMARKS_PER_HAND = 21
HAND_FEATURE_DIM = LANDMARKS_PER_HAND * 3
FEATURE_DIM = 2 * HAND_FEATURE_DIM
MIDDLE_MCP_INDEX = 9


def normalize_hand_keypoints(sequence: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """Apply 2D, wrist translation and per-hand scale normalization."""
    array = np.asarray(sequence, dtype=np.float32)
    if array.ndim != 2 or array.shape[1] != FEATURE_DIM:
        raise ValueError(f"Expected sequence shape (frames, {FEATURE_DIM}), got {array.shape}")

    # MediaPipe x and y are already normalized by frame width and height.
    normalized = array.reshape(-1, 2, LANDMARKS_PER_HAND, 3).copy()
    for frame in normalized:
        for hand in frame:
            if not np.any(hand):
                continue
            wrist = hand[0].copy()
            scale = float(np.linalg.norm(hand[MIDDLE_MCP_INDEX] - wrist))
            hand -= wrist
            hand /= max(scale, epsilon)
    return normalized.reshape(-1, FEATURE_DIM)


def normalize_pixel_xy(
    hand_keypoints: np.ndarray, frame_width: int, frame_height: int
) -> np.ndarray:
    """Normalize pixel x/y coordinates when an extractor does not provide normalized values."""
    normalized = np.asarray(hand_keypoints, dtype=np.float32).copy()
    normalized[..., 0] /= frame_width
    normalized[..., 1] /= frame_height
    return normalized

