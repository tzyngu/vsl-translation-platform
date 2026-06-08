import hashlib
import re
from pathlib import Path

from src.preprocessing.video_reader import VIDEO_EXTENSIONS


def discover_videos(input_dir: str | Path, output_dir: str | Path | None = None) -> list[tuple[str, Path]]:
    """Read dataset/<label>/<video>, excluding report and generated output folders."""
    root = Path(input_dir).resolve()
    excluded = {"processed", "dataset_report", "__pycache__"}
    if output_dir:
        excluded.add(Path(output_dir).resolve().name)
    videos = []
    for label_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if label_dir.name in excluded:
            continue
        for video in sorted(label_dir.iterdir()):
            if video.is_file() and video.suffix.lower() in VIDEO_EXTENSIONS:
                videos.append((label_dir.name, video))
    return videos


def ensure_output_directories(output_dir: str | Path) -> Path:
    root = Path(output_dir)
    for name in ("keypoints", "augmented"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return cleaned or "sample"


def stable_split(relative_video_path: str, train_ratio: float = 0.8, val_ratio: float = 0.1) -> str:
    score = int(hashlib.sha1(relative_video_path.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    if score < train_ratio:
        return "train"
    if score < train_ratio + val_ratio:
        return "validation"
    return "test"

