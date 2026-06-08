from core.models import ModelVersion

from ..config import get_settings


settings = get_settings()


def bootstrap_base_model() -> ModelVersion:
    existing = ModelVersion.objects.filter(is_global_default=True, is_active=True).first()
    if existing:
        return existing
    return ModelVersion.objects.create(
        model_name="transformer_base",
        model_path=settings.base_model_path,
        labels_path=settings.base_labels_path,
        architecture="transformer",
        is_active=True,
        is_global_default=True,
    )


def active_model_for_user(user_id: int) -> ModelVersion:
    return (
        ModelVersion.objects.filter(user_id=user_id, is_active=True).first()
        or ModelVersion.objects.filter(is_global_default=True, is_active=True).first()
        or bootstrap_base_model()
    )

