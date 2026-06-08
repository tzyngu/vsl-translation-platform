#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.augmentation.keypoint_augmentation import (
    apply_gaussian_noise,
    apply_keypoint_dropout,
    apply_keypoint_rotation,
)
from src.augmentation.temporal_augmentation import (
    apply_frame_dropout,
    apply_frame_duplication,
    apply_temporal_crop,
    apply_temporal_shift,
)
from src.preprocessing.mediapipe_extractor import extract_keypoints_from_video
from src.preprocessing.normalization import normalize_hand_keypoints
from src.preprocessing.sequence_sampling import (
    jittered_uniform_sample_sequence,
    uniform_sample_sequence,
)
from src.utils.file_utils import (
    discover_videos,
    ensure_output_directories,
    safe_name,
    stable_split,
)
from src.utils.metadata_writer import LOG_FIELDS, METADATA_FIELDS, write_csv
from src.utils.validation import validate_processed_dataset


def parse_bool(value: str) -> bool:
    if value.lower() in {"1", "true", "yes", "on"}:
        return True
    if value.lower() in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError("Expected true or false")


def sampling_method(num_frames: int, sequence_length: int, jittered: bool = False) -> str:
    if num_frames < sequence_length:
        return "padded_repeat_last"
    return "jittered_uniform" if jittered else "uniform"


def augment_sequence(sequence: np.ndarray, args, rng: np.random.Generator) -> tuple[np.ndarray, list[str]]:
    methods = [
        "temporal_crop", "temporal_shift", "frame_dropout",
        "gaussian_noise", "keypoint_rotation", "keypoint_dropout",
    ]
    augmented = apply_temporal_crop(sequence, target_len=args.sequence_length, rng=rng)
    augmented = apply_temporal_shift(augmented, rng=rng)
    augmented = apply_frame_dropout(augmented, target_len=args.sequence_length, rng=rng)
    if args.use_frame_duplication:
        augmented = apply_frame_duplication(
            augmented, duplication_ratio=args.frame_duplication_ratio,
            target_len=args.sequence_length, rng=rng,
        )
        methods.append("frame_duplication")
    augmented = apply_gaussian_noise(augmented, std=args.noise_std, rng=rng)
    augmented = apply_keypoint_rotation(augmented, rng=rng)
    augmented = apply_keypoint_dropout(augmented, dropout_rate=args.keypoint_dropout_rate, rng=rng)
    return augmented.astype(np.float32), methods


def save_sample(root: Path, relative_path: Path, sequence: np.ndarray) -> None:
    if sequence.shape != (len(sequence), 126) or not np.isfinite(sequence).all():
        raise ValueError(f"Invalid processed sequence: shape={sequence.shape}")
    destination = root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    np.save(destination, sequence.astype(np.float32))


def process_dataset(args) -> dict:
    input_dir = Path(args.input_dir).resolve()
    output_dir = ensure_output_directories(args.output_dir).resolve()
    videos = discover_videos(input_dir, output_dir)
    metadata: list[dict] = []
    errors: list[dict] = []
    reviews: list[dict] = []
    rng = np.random.default_rng(args.seed)

    for video_index, (label, video_path) in enumerate(videos, start=1):
        relative_video = video_path.relative_to(input_dir).as_posix()
        split = stable_split(relative_video, args.train_ratio, args.val_ratio)
        sample_base = f"{safe_name(label)}_{video_index:06d}"
        try:
            raw_sequence, original_frames, valid_frames = extract_keypoints_from_video(video_path)
            if valid_frames == 0:
                errors.append({"original_video_path": str(video_path), "label_name": label, "reason": "No detected hand keypoints"})
                continue
            if valid_frames < args.min_valid_frames:
                reviews.append({"original_video_path": str(video_path), "label_name": label, "reason": f"Only {valid_frames} valid keypoint frames; skipped"})
                continue

            normalized = normalize_hand_keypoints(raw_sequence)
            main = uniform_sample_sequence(normalized, args.sequence_length)
            main_path = Path("keypoints") / label / f"{sample_base}.npy"
            save_sample(output_dir, main_path, main)
            add_metadata(metadata, sample_base, video_path, label, main_path, split, "main_uniform",
                         sampling_method(len(normalized), args.sequence_length), "", args, original_frames, valid_frames)

            if split == "train":
                for number in range(1, args.num_jittered_samples + 1):
                    jittered = jittered_uniform_sample_sequence(normalized, args.sequence_length, rng)
                    jitter_id = f"{sample_base}_jitter_{number:03d}"
                    jitter_path = Path("augmented") / label / f"{jitter_id}.npy"
                    save_sample(output_dir, jitter_path, jittered)
                    add_metadata(metadata, jitter_id, video_path, label, jitter_path, split, "jittered_sampling",
                                 sampling_method(len(normalized), args.sequence_length, True), "", args, original_frames, valid_frames)
                for number in range(1, args.augment_per_sample + 1):
                    augmented, methods = augment_sequence(main, args, rng)
                    aug_id = f"{sample_base}_aug_{number:03d}"
                    aug_path = Path("augmented") / label / f"{aug_id}.npy"
                    save_sample(output_dir, aug_path, augmented)
                    add_metadata(metadata, aug_id, video_path, label, aug_path, split, "augmented",
                                 sampling_method(len(normalized), args.sequence_length), "|".join(methods), args, original_frames, valid_frames)
        except Exception as exc:
            errors.append({"original_video_path": str(video_path), "label_name": label, "reason": f"{type(exc).__name__}: {exc}"})
        if video_index % 25 == 0 or video_index == len(videos):
            print(f"Processed {video_index}/{len(videos)} videos", flush=True)

    write_csv(output_dir / "metadata.csv", metadata, METADATA_FIELDS)
    write_csv(output_dir / "error_log.csv", errors, LOG_FIELDS)
    write_csv(output_dir / "review_log.csv", reviews, LOG_FIELDS)
    result = validate_processed_dataset(output_dir, args.sequence_length)
    print(f"Saved {len(metadata)} samples; errors={len(errors)}; review={len(reviews)}")
    print(f"Validation: {'PASS' if result['valid'] else 'FAIL'} ({result['npy_files']} npy files)")
    for error in result["errors"]:
        print(f"- {error}")
    return result


def add_metadata(rows, sample_id, video_path, label, output_path, split, sample_type,
                 method, augmentation_methods, args, original_frames, valid_frames) -> None:
    rows.append({
        "sample_id": sample_id, "original_video_path": str(video_path), "label_name": label,
        "output_keypoints_path": output_path.as_posix(), "split": split, "sample_type": sample_type,
        "sampling_method": method, "augmentation_methods": augmentation_methods,
        "sequence_length": args.sequence_length, "feature_dim": 126,
        "num_original_frames": original_frames, "num_valid_frames": valid_frames, "status": "ok",
    })


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert VSL videos to normalized MediaPipe hand keypoints.")
    parser.add_argument("--input_dir", default="dataset", help="Folder containing one subfolder per label.")
    parser.add_argument("--output_dir", default="dataset/processed")
    parser.add_argument("--sequence_length", type=int, default=30)
    parser.add_argument("--num_jittered_samples", type=int, default=2)
    parser.add_argument("--augment_per_sample", type=int, default=3)
    parser.add_argument("--use_frame_duplication", type=parse_bool, default=False)
    parser.add_argument("--frame_duplication_ratio", type=float, default=0.05)
    parser.add_argument("--noise_std", type=float, default=0.01)
    parser.add_argument("--keypoint_dropout_rate", type=float, default=0.03)
    parser.add_argument("--min_valid_frames", type=int, default=5)
    parser.add_argument("--train_ratio", type=float, default=0.8)
    parser.add_argument("--val_ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser


if __name__ == "__main__":
    result = process_dataset(build_parser().parse_args())
    raise SystemExit(0 if result["valid"] else 1)

