from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..schemas import LoginRequest, RegisterRequest
from ..security import COOKIE_NAME, create_access_token, current_user


router = APIRouter(prefix="/auth", tags=["auth"])


def public_user(user: User) -> dict:
    return {
        "_id": str(user.pk), "username": user.username, "email": user.email,
        "role": "admin" if user.is_superuser else "user", "is_superuser": user.is_superuser,
        "created_at": user.date_joined.isoformat(),
    }


@router.post("/register")
def register(payload: RegisterRequest, response: Response):
    if User.objects.filter(email__iexact=payload.email.strip()).exists():
        raise HTTPException(status_code=409, detail="Email already exists")
    try:
        user = User.objects.create_user(
            username=payload.username.strip(), email=payload.email.lower().strip(), password=payload.password
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Username already exists") from exc
    response.set_cookie(COOKIE_NAME, create_access_token(user.pk), httponly=True, samesite="lax")
    return public_user(user)


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    user = authenticate(username=payload.username.strip(), password=payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    response.set_cookie(COOKIE_NAME, create_access_token(user.pk), httponly=True, samesite="lax")
    return public_user(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(user=Depends(current_user)):
    return public_user(user)
