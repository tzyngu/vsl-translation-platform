import csv
from pathlib import Path

import numpy as np

from .metadata_writer import METADATA_FIELDS


def validate_processed_dataset(output_dir: str | Path, sequence_length: int = 30) -> dict:
    root = Path(output_dir)
    errors: list[str] = []
    npy_files = list(root.rglob("*.npy"))
    for path in npy_files:
        array = np.load(path)
        if array.shape != (sequence_length, 126):
            errors.append(f"{path}: expected {(sequence_length, 126)}, got {array.shape}")
        if not np.isfinite(array).all():
            errors.append(f"{path}: contains NaN or Inf")

    metadata_path = root / "metadata.csv"
    if not metadata_path.exists():
        errors.append(f"{metadata_path}: missing")
        metadata_rows = 0
    else:
        with metadata_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            missing_columns = sorted(set(METADATA_FIELDS) - set(reader.fieldnames or []))
            if missing_columns:
                errors.append(f"{metadata_path}: missing columns {missing_columns}")
            metadata_rows = sum(1 for _ in reader)
    for log_name in ("error_log.csv", "review_log.csv"):
        if not (root / log_name).exists():
            errors.append(f"{root / log_name}: missing")
    return {"valid": not errors, "npy_files": len(npy_files), "metadata_rows": metadata_rows, "errors": errors}

