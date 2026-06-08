from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_db: str = "vsl_system"
    postgres_user: str = "vsl_user"
    postgres_password: str = "vsl_local_password"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    jwt_secret: str = "change-this-before-production"
    jwt_expire_minutes: int = 1440
    frontend_origin: str = "http://127.0.0.1:8000"
    backend_url: str = "http://127.0.0.1:8001"
    media_root: str = "media"
    base_model_path: str = "training_outputs/final_models/transformer.keras"
    base_labels_path: str = "training_outputs/label_classes.json"
    hand_landmarker_path: str = "models/hand_landmarker.task"
    openai_enabled: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-5"
    predict_every_n_frames: int = 4
    confidence_threshold: float = 0.70
    stability_window: int = 5
    stability_min_count: int = 3
    word_cooldown_seconds: float = 1.5

    def project_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def media_path(self) -> Path:
        return self.project_path(self.media_root)


@lru_cache
def get_settings() -> Settings:
    return Settings()
