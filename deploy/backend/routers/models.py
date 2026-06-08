from django.db.models import Q
from fastapi import APIRouter, Depends

from core.models import ModelVersion
from ..security import current_user
from ..services.model_registry import active_model_for_user
from ..utils import serialize


router = APIRouter(prefix="/models", tags=["models"])


def model_dict(model: ModelVersion) -> dict:
    return serialize({
        "_id": model.pk, "user_id": model.user_id, "model_name": model.model_name,
        "model_path": model.model_path, "labels_path": model.labels_path,
        "architecture": model.architecture, "is_active": model.is_active,
        "is_global_default": model.is_global_default, "created_at": model.created_at,
    })


@router.get("")
def list_models(user=Depends(current_user)):
    return [model_dict(item) for item in ModelVersion.objects.filter(Q(user=user) | Q(is_global_default=True))]


@router.get("/active")
def active_model(user=Depends(current_user)):
    return model_dict(active_model_for_user(user.pk))

