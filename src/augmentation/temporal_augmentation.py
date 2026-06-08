import numpy as np

from src.preprocessing.sequence_sampling import resample_sequence


def apply_temporal_crop(
    sequence: np.ndarray,
    crop_ratio_range: tuple[float, float] = (0.85, 1.0),
    target_len: int = 30,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng or np.random.default_rng()
    crop_len = max(1, int(round(len(sequence) * rng.uniform(*crop_ratio_range))))
    start = int(rng.integers(0, len(sequence) - crop_len + 1))
    return resample_sequence(sequence[start : start + crop_len], target_len)


def apply_temporal_shift(
    sequence: np.ndarray,
    shift_range: tuple[int, int] = (-3, 3),
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng or np.random.default_rng()
    shift = int(rng.integers(shift_range[0], shift_range[1] + 1))
    if shift > 0:
        return np.concatenate([np.repeat(sequence[:1], shift, axis=0), sequence[:-shift]])
    if shift < 0:
        return np.concatenate([sequence[-shift:], np.repeat(sequence[-1:], -shift, axis=0)])
    return np.asarray(sequence, dtype=np.float32).copy()


def apply_frame_dropout(
    sequence: np.ndarray,
    dropout_ratio: float = 0.10,
    target_len: int = 30,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng or np.random.default_rng()
    keep = rng.random(len(sequence)) >= dropout_ratio
    if not np.any(keep):
        keep[int(rng.integers(0, len(sequence)))] = True
    return resample_sequence(sequence[keep], target_len)


def apply_frame_duplication(
    sequence: np.ndarray,
    duplication_ratio: float = 0.05,
    target_len: int = 30,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng or np.random.default_rng()
    extra_count = max(1, int(round(len(sequence) * duplication_ratio)))
    duplicate_indices = set(rng.choice(len(sequence), size=extra_count, replace=False).tolist())
    frames = []
    for index, frame in enumerate(sequence):
        frames.append(frame)
        if index in duplicate_indices:
            frames.append(frame.copy())
    return resample_sequence(np.asarray(frames), target_len)

