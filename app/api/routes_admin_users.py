from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.dependencies.auth import get_current_user, get_db, require_roles
from app.models.admin_user import AdminUser
from app.schemas.admin_user import (
    AdminUserCreate,
    AdminUserRead,
    AdminUserResetPassword,
    AdminUserStatusUpdate,
    AdminUserUpdate,
)
from app.schemas.common import DetailResponse, ListResponse, MetaData
from app.services.serializers import serialize_admin_user

router = APIRouter(prefix="/dashboard/admin-users", tags=["dashboard-admin-users"])


def get_admin_or_404(db: Session, user_id: uuid.UUID) -> AdminUser:
    user = db.get(AdminUser, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")
    return user


@router.get("", response_model=ListResponse[AdminUserRead], dependencies=[Depends(require_roles("superadmin"))])
def list_admin_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(AdminUser)
    count_query = select(func.count()).select_from(AdminUser)

    if search:
        term = f"%{search.lower()}%"
        query = query.where(func.lower(AdminUser.username).like(term))
        count_query = count_query.where(func.lower(AdminUser.username).like(term))

    total = db.scalar(count_query) or 0
    rows = db.scalars(query.order_by(AdminUser.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return ListResponse(data=[serialize_admin_user(item) for item in rows], meta=MetaData.from_pagination(page, page_size, total))


@router.post("", response_model=DetailResponse[AdminUserRead], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("superadmin"))])
def create_admin_user(payload: AdminUserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(AdminUser).where(AdminUser.username == payload.username))
    if existing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Username already exists")

    user = AdminUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return DetailResponse(data=serialize_admin_user(user))


@router.get("/{user_id}", response_model=DetailResponse[AdminUserRead], dependencies=[Depends(require_roles("superadmin"))])
def get_admin_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return DetailResponse(data=serialize_admin_user(get_admin_or_404(db, user_id)))


@router.put("/{user_id}", response_model=DetailResponse[AdminUserRead], dependencies=[Depends(require_roles("superadmin"))])
def update_admin_user(user_id: uuid.UUID, payload: AdminUserUpdate, db: Session = Depends(get_db)):
    user = get_admin_or_404(db, user_id)
    other = db.scalar(select(AdminUser).where(AdminUser.username == payload.username, AdminUser.id != user_id))
    if other:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Username already exists")

    user.username = payload.username
    user.role = payload.role
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return DetailResponse(data=serialize_admin_user(user))


@router.patch("/{user_id}/status", response_model=DetailResponse[AdminUserRead], dependencies=[Depends(require_roles("superadmin"))])
def update_admin_user_status(
    user_id: uuid.UUID,
    payload: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    user = get_admin_or_404(db, user_id)
    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Cannot deactivate current user")

    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return DetailResponse(data=serialize_admin_user(user))


@router.post("/{user_id}/reset-password", response_model=DetailResponse[AdminUserRead], dependencies=[Depends(require_roles("superadmin"))])
def reset_admin_password(user_id: uuid.UUID, payload: AdminUserResetPassword, db: Session = Depends(get_db)):
    user = get_admin_or_404(db, user_id)
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    return DetailResponse(data=serialize_admin_user(user))
