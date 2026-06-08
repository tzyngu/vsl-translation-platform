from datetime import timedelta

import jwt
from django.contrib.auth.models import User
from fastapi import Cookie, Depends, Header, HTTPException, status

from .config import get_settings
from .database import setup_django


setup_django()
settings = get_settings()
COOKIE_NAME = "vsl_access_token"


def create_access_token(user_id: int) -> str:
    from django.utils import timezone

    expires_at = timezone.now() + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def current_user(
    authorization: str | None = Header(default=None),
    vsl_access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> User:
    token = authorization.removeprefix("Bearer ").strip() if authorization and authorization.startswith("Bearer ") else vsl_access_token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return User.objects.get(pk=decode_access_token(token), is_active=True)
    except User.DoesNotExist as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found") from exc


def current_admin(user: User = Depends(current_user)) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user
