from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import LoginRateLimiter
from app.core.config import Settings
from app.core.security import create_access_token, verify_password
from app.dependencies.auth import get_current_user, get_db, get_settings
from app.models.admin_user import AdminUser
from app.schemas.auth import AuthUser, LoginRequest, LoginResponse
from app.schemas.common import DetailResponse
from app.services.serializers import serialize_auth_user

router = APIRouter(prefix="/dashboard/auth", tags=["dashboard-auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    limiter: LoginRateLimiter = request.app.state.login_rate_limiter
    key = payload.username.strip().lower()
    if not limiter.check(key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")

    user = db.scalar(select(AdminUser).where(AdminUser.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        limiter.add_failure(key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    limiter.reset(key)
    token = create_access_token(str(user.id), settings, extra={"role": user.role})
    return LoginResponse(access_token=token, user=serialize_auth_user(user))


@router.post("/logout")
def logout():
    return {"message": "Logged out"}


@router.get("/me", response_model=DetailResponse[AuthUser])
def me(current_user: AdminUser = Depends(get_current_user)):
    return DetailResponse(data=serialize_auth_user(current_user))
