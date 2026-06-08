import uuid

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    AVATAR_CHOICES = [
        ("avatar1.png", "Avatar 1"),
        ("avatar2.png", "Avatar 2"),
        ("avatar3.png", "Avatar 3"),
        ("avatar4.png", "Avatar 4"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.CharField(max_length=20, choices=AVATAR_CHOICES)

    def __str__(self):
        return f"{self.user.username} profile"


class Gesture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gestures")
    label_name = models.CharField(max_length=80)
    display_name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    num_samples = models.PositiveIntegerField(default=0)
    source_gesture = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["owner", "label_name"])]

    def __str__(self):
        return f"{self.display_name} ({self.label_name})"


class UploadedSample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_samples")
    gesture = models.ForeignKey(Gesture, on_delete=models.CASCADE, related_name="samples")
    video_path = models.TextField(null=True, blank=True)
    keypoint_path = models.TextField()
    status = models.CharField(max_length=30, default="processed")
    source_sample = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    is_import_snapshot = models.BooleanField(default=False)
    num_original_frames = models.PositiveIntegerField(null=True, blank=True)
    num_valid_frames = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ModelVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="model_versions")
    model_name = models.CharField(max_length=120)
    model_path = models.TextField()
    labels_path = models.TextField()
    architecture = models.CharField(max_length=80)
    metrics = models.JSONField(default=dict, blank=True)
    training_config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=False)
    is_global_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.model_name


class TrainingJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="training_jobs")
    model_version = models.ForeignKey(ModelVersion, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, default="pending")
    message = models.TextField(blank=True)
    logs = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)


class SharedGesture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gesture = models.OneToOneField(Gesture, on_delete=models.CASCADE, related_name="share_record")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_gestures")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ImportedGesture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    imported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gesture_imports")
    source_gesture = models.ForeignKey(Gesture, null=True, on_delete=models.SET_NULL, related_name="imports")
    new_gesture = models.OneToOneField(Gesture, on_delete=models.CASCADE, related_name="import_record")
    created_at = models.DateTimeField(auto_now_add=True)


class PredictionHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="predictions")
    label = models.CharField(max_length=120)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)


class TranslationHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="translations")
    labels = models.JSONField(default=list)
    sentence = models.TextField()
    provider = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
