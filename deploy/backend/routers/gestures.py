import shutil
from pathlib import Path

from asgiref.sync import sync_to_async
from django.db import transaction
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.models import Gesture, ImportedGesture, SharedGesture, UploadedSample
from ..config import get_settings
from ..schemas import GestureCreate
from ..security import current_user
from ..services.upload_service import save_and_process_upload
from ..utils import serialize


router = APIRouter(prefix="/gestures", tags=["gestures"])
settings = get_settings()


def gesture_dict(gesture: Gesture, include_owner: bool = False) -> dict:
    data = {
        "_id": gesture.pk, "owner_id": gesture.owner_id, "label_name": gesture.label_name,
        "display_name": gesture.display_name, "description": gesture.description,
        "is_public": gesture.is_public, "num_samples": gesture.num_samples,
        "created_at": gesture.created_at,
    }
    if include_owner:
        try:
            avatar = gesture.owner.profile.avatar
        except AttributeError:
            avatar = "avatar1.png"
        data.update({
            "owner_username": gesture.owner.username,
            "owner_avatar_url": f"/static/images/{avatar}",
        })
    return serialize(data)


def sample_dict(sample: UploadedSample) -> dict:
    return serialize({
        "_id": sample.pk, "user_id": sample.user_id, "gesture_id": sample.gesture_id,
        "video_path": sample.video_path, "keypoint_path": sample.keypoint_path,
        "status": sample.status, "num_original_frames": sample.num_original_frames,
        "num_valid_frames": sample.num_valid_frames, "created_at": sample.created_at,
    })


@router.get("")
def list_gestures(user=Depends(current_user)):
    return [gesture_dict(item) for item in Gesture.objects.filter(owner=user).order_by("-created_at")]


@router.post("")
def create_gesture(payload: GestureCreate, user=Depends(current_user)):
    gesture = Gesture.objects.create(
        owner=user, label_name=payload.label_name.strip(), display_name=payload.display_name.strip(),
        description=payload.description.strip(), is_public=payload.is_public,
    )
    if gesture.is_public:
        SharedGesture.objects.create(gesture=gesture, owner=user)
    return gesture_dict(gesture)


@router.post("/{gesture_id}/samples")
async def upload_samples(gesture_id: str, files: list[UploadFile] = File(...), user=Depends(current_user)):
    try:
        gesture = await sync_to_async(Gesture.objects.get)(pk=gesture_id, owner=user)
    except (Gesture.DoesNotExist, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Gesture not found") from exc
    processed, errors = [], []
    for upload in files:
        try:
            processed.append(sample_dict(await save_and_process_upload(user.pk, gesture.pk, upload)))
        except Exception as exc:
            errors.append({"filename": upload.filename, "detail": str(exc)})
    return {"processed": processed, "errors": errors}


@router.get("/public")
def public_library(user=Depends(current_user)):
    items = (
        Gesture.objects.filter(is_public=True)
        .exclude(owner=user)
        .select_related("owner", "owner__profile")
        .order_by("-created_at")
    )
    return [gesture_dict(item, include_owner=True) for item in items]


@router.post("/{gesture_id}/import")
def import_gesture(gesture_id: str, user=Depends(current_user)):
    try:
        source = Gesture.objects.get(pk=gesture_id, is_public=True)
    except (Gesture.DoesNotExist, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Public gesture not found") from exc

    with transaction.atomic():
        source_samples = list(source.samples.filter(status="processed"))
        imported = Gesture.objects.create(
            owner=user, label_name=source.label_name, display_name=source.display_name,
            description=source.description, source_gesture=source, num_samples=len(source_samples),
        )
        snapshot_dir = settings.media_path / "keypoints" / str(user.pk) / str(imported.pk)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        for source_sample in source_samples:
            snapshot = UploadedSample(
                user=user, gesture=imported, keypoint_path="", status="processed",
                source_sample=source_sample, is_import_snapshot=True,
                num_original_frames=source_sample.num_original_frames, num_valid_frames=source_sample.num_valid_frames,
            )
            snapshot_path = snapshot_dir / f"{snapshot.pk}.npy"
            shutil.copy2(Path(source_sample.keypoint_path), snapshot_path)
            snapshot.keypoint_path = str(snapshot_path)
            snapshot.save()
        ImportedGesture.objects.create(imported_by=user, source_gesture=source, new_gesture=imported)
    return gesture_dict(imported)
