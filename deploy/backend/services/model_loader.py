import json
import threading
from pathlib import Path

import numpy as np

from ..config import get_settings
from .custom_layers import positional_embedding_class


settings = get_settings()


class LoadedModel:
    def __init__(self, model_path: Path, labels_path: Path):
        import tensorflow as tf

        self.model_path = model_path
        self.labels_path = labels_path
        self.labels = json.loads(labels_path.read_text(encoding="utf-8"))
        positional_embedding = positional_embedding_class()
        custom_objects = {
            "PositionalEmbedding": positional_embedding,
            "VSL>PositionalEmbedding": positional_embedding,
        }
        self.model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
        output_classes = int(self.model.output_shape[-1])
        if output_classes != len(self.labels):
            raise ValueError(f"Model has {output_classes} outputs but labels file has {len(self.labels)} labels")

    def predict(self, sequence: np.ndarray) -> dict:
        array = np.asarray(sequence, dtype=np.float32)
        if array.shape != (30, 126):
            raise ValueError(f"Expected sequence shape (30, 126), got {array.shape}")
        probabilities = self.model(array[None, ...], training=False).numpy()[0]
        label_index = int(np.argmax(probabilities))
        return {"label": self.labels[label_index], "confidence": float(probabilities[label_index])}


class ModelCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._models: dict[tuple[str, str], LoadedModel] = {}

    def get(self, model_path: Path, labels_path: Path) -> LoadedModel:
        key = (str(model_path.resolve()), str(labels_path.resolve()))
        with self._lock:
            if key not in self._models:
                self._models[key] = LoadedModel(model_path, labels_path)
            return self._models[key]


model_cache = ModelCache()


def load_base_model() -> LoadedModel:
    return model_cache.get(
        settings.project_path(settings.base_model_path),
        settings.project_path(settings.base_labels_path),
    )
