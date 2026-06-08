import csv
from pathlib import Path


METADATA_FIELDS = [
    "sample_id", "original_video_path", "label_name", "output_keypoints_path",
    "split", "sample_type", "sampling_method", "augmentation_methods",
    "sequence_length", "feature_dim", "num_original_frames", "num_valid_frames", "status",
]
LOG_FIELDS = ["original_video_path", "label_name", "reason"]


def write_csv(path: str | Path, rows: list[dict], fieldnames: list[str]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

