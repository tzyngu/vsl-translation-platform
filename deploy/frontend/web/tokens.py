from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone


def create_access_token(user_id: int) -> str:
    expires_at = timezone.now() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, settings.JWT_SECRET, algorithm="HS256")
