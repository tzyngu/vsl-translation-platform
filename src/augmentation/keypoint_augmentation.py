import numpy as np


def _as_hands(sequence: np.ndarray) -> np.ndarray:
    return np.asarray(sequence, dtype=np.float32).reshape(-1, 2, 21, 3).copy()


def apply_gaussian_noise(
    sequence: np.ndarray,
    std: float = 0.01,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng or np.random.default_rng()
    hands = _as_hands(sequence)
    for hand in hands.reshape(-1, 21, 3):
        if np.any(hand):
            hand += rng.normal(0.0, std, size=hand.shape).astype(np.float32)
    return hands.reshape(-1, 126)


def apply_keypoint_rotation(
    sequence: np.ndarray,
    angle_range: tuple[float, float] = (-5.0, 5.0),
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng or np.random.default_rng()
    hands = _as_hands(sequence)
    for hand in hands.reshape(-1, 21, 3):
        if not np.any(hand):
            continue
        radians = np.deg2rad(rng.uniform(*angle_range))
        cosine, sine = np.cos(radians), np.sin(radians)
        xy = hand[:, :2].copy()
        hand[:, 0] = cosine * xy[:, 0] - sine * xy[:, 1]
        hand[:, 1] = sine * xy[:, 0] + cosine * xy[:, 1]
    return hands.reshape(-1, 126)


def apply_keypoint_dropout(
    sequence: np.ndarray,
    dropout_rate: float = 0.03,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng or np.random.default_rng()
    hands = _as_hands(sequence)
    for hand in hands.reshape(-1, 21, 3):
        if np.any(hand):
            hand[rng.random(21) < dropout_rate] = 0.0
    return hands.reshape(-1, 126)

