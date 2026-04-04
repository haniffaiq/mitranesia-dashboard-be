from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import decode_access_token
from app.models.admin_user import AdminUser


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request):
    session_local = request.app.state.session_local
    db: Session = session_local()
    try:
        yield db
    finally:
        db.close()


def get_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return authorization.split(" ", 1)[1]


def get_current_user(
    token: str = Depends(get_token),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AdminUser:
    try:
        payload = decode_access_token(token, settings)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing subject")
        admin_id = uuid.UUID(user_id)
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = db.get(AdminUser, admin_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


def require_roles(*roles: str):
    def dependency(current_user: AdminUser = Depends(get_current_user)) -> AdminUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return dependency
