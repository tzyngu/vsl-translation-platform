import unittest

import numpy as np

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
from src.preprocessing.normalization import normalize_hand_keypoints
from src.preprocessing.sequence_sampling import (
    jittered_uniform_sample_sequence,
    uniform_sample_sequence,
)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(7)
        self.raw = np.zeros((45, 126), dtype=np.float32)
        left_hand = self.raw[:, :63].reshape(45, 21, 3)
        left_hand[:] = self.rng.normal(size=left_hand.shape)
        left_hand[:, 0] = [0.2, 0.3, 0.1]
        left_hand[:, 9] = [0.4, 0.3, 0.1]
        self.normalized = normalize_hand_keypoints(self.raw)

    def test_normalization_keeps_missing_hand_zero(self):
        self.assertEqual(self.normalized.shape, (45, 126))
        self.assertEqual(np.count_nonzero(self.normalized[:, 63:]), 0)
        self.assertEqual(np.count_nonzero(self.normalized[:, :3]), 0)

    def test_short_sequence_repeats_last_frame(self):
        sampled = uniform_sample_sequence(self.normalized[:18], 30)
        self.assertEqual(sampled.shape, (30, 126))
        self.assertTrue(np.array_equal(sampled[-1], self.normalized[17]))

    def test_uniform_and_jittered_sampling_cover_target_length(self):
        uniform = uniform_sample_sequence(self.normalized, 30)
        jittered = jittered_uniform_sample_sequence(self.normalized, 30, self.rng)
        self.assertEqual(uniform.shape, (30, 126))
        self.assertEqual(jittered.shape, (30, 126))
        self.assertTrue(np.array_equal(uniform[0], self.normalized[0]))
        self.assertTrue(np.array_equal(uniform[-1], self.normalized[-1]))

    def test_augmentation_keeps_missing_hand_zero(self):
        augmented = uniform_sample_sequence(self.normalized, 30)
        augmented = apply_temporal_crop(augmented, rng=self.rng)
        augmented = apply_temporal_shift(augmented, rng=self.rng)
        augmented = apply_frame_dropout(augmented, rng=self.rng)
        augmented = apply_frame_duplication(augmented, rng=self.rng)
        augmented = apply_gaussian_noise(augmented, rng=self.rng)
        augmented = apply_keypoint_rotation(augmented, rng=self.rng)
        augmented = apply_keypoint_dropout(augmented, rng=self.rng)
        self.assertEqual(augmented.shape, (30, 126))
        self.assertTrue(np.isfinite(augmented).all())
        self.assertEqual(np.count_nonzero(augmented[:, 63:]), 0)


if __name__ == "__main__":
    unittest.main()
