from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.models.admin_user import AdminUser


def seed_default_superadmin(db: Session, settings: Settings) -> None:
    existing = db.scalar(select(AdminUser).where(AdminUser.username == settings.default_superadmin_username))
    if existing:
        return

    db.add(
        AdminUser(
            username=settings.default_superadmin_username,
            password_hash=hash_password(settings.default_superadmin_password),
            role="superadmin",
            is_active=True,
        )
    )
    db.commit()
