import base64
import time
from collections import Counter, deque

import cv2
import numpy as np

from src.preprocessing.normalization import normalize_hand_keypoints

from ..config import get_settings
from .label_display import display_label
from .model_loader import model_cache


settings = get_settings()


class RealtimeSession:
    def __init__(self, model_path, labels_path):
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        self.mp = mp
        self.vision = vision
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(settings.project_path(settings.hand_landmarker_path))),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.model = model_cache.get(settings.project_path(model_path), settings.project_path(labels_path))
        self.sequence = deque(maxlen=30)
        self.hand_presence = deque(maxlen=settings.stability_window)
        self.recent_predictions = deque(maxlen=settings.stability_window)
        self.frame_index = 0
        self.last_word = None
        self.last_word_at = 0.0

    def close(self):
        self.landmarker.close()

    def process_base64_jpeg(self, encoded_frame: str) -> dict:
        started = time.perf_counter()
        jpeg = base64.b64decode(encoded_frame.split(",", 1)[-1])
        frame = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid JPEG frame")
        frame = cv2.resize(frame, (640, 480))
        rgb = frame[:, :, ::-1]
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        result = self.landmarker.detect_for_video(image, int(time.monotonic() * 1000))
        feature = np.zeros((2, 21, 3), dtype=np.float32)
        for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
            index = 0 if handedness[0].category_name.lower() == "left" else 1
            feature[index] = [[point.x, point.y, point.z] for point in landmarks]
        hands_detected = bool(np.any(feature))
        self.sequence.append(normalize_hand_keypoints(feature.reshape(1, 126))[0])
        self.hand_presence.append(hands_detected)
        self.frame_index += 1

        response = {
            "hands_detected": hands_detected,
            "window_frames": len(self.sequence),
            "prediction": None,
            "accepted_word": None,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        if (
            len(self.sequence) < 30
            or self.frame_index % settings.predict_every_n_frames
            or sum(self.hand_presence) < settings.stability_min_count
        ):
            return response

        prediction = self.model.predict(np.asarray(self.sequence))
        prediction["display_label"] = display_label(prediction["label"])
        response["prediction"] = prediction
        if prediction["confidence"] < settings.confidence_threshold:
            return response
        self.recent_predictions.append(prediction["label"])
        stable_label, count = Counter(self.recent_predictions).most_common(1)[0]
        now = time.monotonic()
        if (
            count >= settings.stability_min_count
            and (stable_label != self.last_word or now - self.last_word_at >= settings.word_cooldown_seconds)
        ):
            response["accepted_word"] = stable_label
            response["accepted_display_word"] = display_label(stable_label)
            self.last_word = stable_label
            self.last_word_at = now
        return response
