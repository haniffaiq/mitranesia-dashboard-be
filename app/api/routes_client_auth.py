from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies.client_auth import get_current_client_user, get_db, get_settings
from app.models.client_user import ClientUser
from app.schemas.client_auth import ClientAuthResponse, ClientAuthUser, ClientLoginRequest, ClientRegisterRequest
from app.schemas.common import DetailResponse
from app.services.serializers import iso

router = APIRouter(prefix="/client/auth", tags=["client-auth"])


def serialize_client_auth_user(user: ClientUser) -> ClientAuthUser:
    return ClientAuthUser(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        is_active=user.is_active,
        created_at=iso(user.created_at) or "",
        updated_at=iso(user.updated_at) or "",
    )


@router.post("/register", response_model=ClientAuthResponse, status_code=status.HTTP_201_CREATED)
def register_client(
    payload: ClientRegisterRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    existing = db.scalar(select(ClientUser).where(ClientUser.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Email already exists")

    user = ClientUser(
        full_name=payload.full_name,
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), settings, extra={"token_type": "client"})
    return ClientAuthResponse(access_token=token, user=serialize_client_auth_user(user))


@router.post("/login", response_model=ClientAuthResponse)
def login_client(
    payload: ClientLoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = db.scalar(select(ClientUser).where(ClientUser.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    token = create_access_token(str(user.id), settings, extra={"token_type": "client"})
    return ClientAuthResponse(access_token=token, user=serialize_client_auth_user(user))


@router.get("/me", response_model=DetailResponse[ClientAuthUser])
def client_me(current_user: ClientUser = Depends(get_current_client_user)):
    return DetailResponse(data=serialize_client_auth_user(current_user))


@router.post("/logout")
def client_logout():
    return {"message": "Logged out"}
