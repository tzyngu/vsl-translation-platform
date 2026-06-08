import numpy as np


def pad_sequence_repeat_last(sequence: np.ndarray, target_len: int = 30) -> np.ndarray:
    if len(sequence) == 0:
        raise ValueError("Cannot pad an empty sequence")
    if len(sequence) >= target_len:
        return np.asarray(sequence[:target_len], dtype=np.float32).copy()
    padding = np.repeat(sequence[-1:], target_len - len(sequence), axis=0)
    return np.concatenate([sequence, padding], axis=0).astype(np.float32, copy=False)


def uniform_sample_sequence(sequence: np.ndarray, target_len: int = 30) -> np.ndarray:
    """Sample the full action, or repeat the last frame when a video is short."""
    if len(sequence) == 0:
        raise ValueError("Cannot sample an empty sequence")
    # sequence_length=30 does not mean taking only the first 30 frames.
    # Long videos are sampled across the whole action; short videos repeat the last frame.
    if len(sequence) < target_len:
        return pad_sequence_repeat_last(sequence, target_len)
    if len(sequence) == target_len:
        return np.asarray(sequence, dtype=np.float32).copy()
    indices = np.linspace(0, len(sequence) - 1, target_len).astype(int)
    return np.asarray(sequence[indices], dtype=np.float32)


def jittered_uniform_sample_sequence(
    sequence: np.ndarray,
    target_len: int = 30,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Choose one random frame per evenly spaced bin across the complete action."""
    if len(sequence) == 0:
        raise ValueError("Cannot sample an empty sequence")
    if len(sequence) <= target_len:
        return pad_sequence_repeat_last(sequence, target_len)
    rng = rng or np.random.default_rng()
    edges = np.linspace(0, len(sequence), target_len + 1).astype(int)
    indices = [rng.integers(edges[i], max(edges[i] + 1, edges[i + 1])) for i in range(target_len)]
    return np.asarray(sequence[indices], dtype=np.float32)


def resample_sequence(sequence: np.ndarray, target_len: int = 30) -> np.ndarray:
    return uniform_sample_sequence(sequence, target_len)

