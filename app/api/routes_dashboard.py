from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db, require_roles
from app.schemas.common import DetailResponse
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DetailResponse[DashboardSummary], dependencies=[Depends(require_roles("superadmin", "admin", "editor"))])
def dashboard_summary(db: Session = Depends(get_db)):
    return DetailResponse(data=get_dashboard_summary(db))
