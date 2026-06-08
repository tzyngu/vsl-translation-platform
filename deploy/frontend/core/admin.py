from django.contrib import admin

from .models import (
    Gesture, ImportedGesture, ModelVersion, PredictionHistory, SharedGesture,
    TrainingJob, TranslationHistory, UploadedSample, UserProfile,
)


for model in (
    Gesture, UploadedSample, ModelVersion, TrainingJob, SharedGesture,
    ImportedGesture, PredictionHistory, TranslationHistory, UserProfile,
):
    admin.site.register(model)
