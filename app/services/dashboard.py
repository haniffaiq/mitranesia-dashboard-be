from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.admin_user import AdminUser
from app.models.insight_article import InsightArticle
from app.models.merchant import Merchant
from app.schemas.dashboard import CountByBucket, DashboardSummary
from app.services.serializers import serialize_merchant


def get_dashboard_summary(db: Session) -> DashboardSummary:
    total_merchants = db.scalar(select(func.count()).select_from(Merchant)) or 0
    active_merchants = db.scalar(select(func.count()).select_from(Merchant).where(Merchant.is_active.is_(True))) or 0
    total_insights = db.scalar(select(func.count()).select_from(InsightArticle)) or 0
    total_admin_users = db.scalar(select(func.count()).select_from(AdminUser)) or 0

    category_rows = db.execute(
        select(Merchant.category, func.count()).group_by(Merchant.category).order_by(func.count().desc(), Merchant.category.asc())
    ).all()
    type_rows = db.execute(
        select(Merchant.type, func.count()).group_by(Merchant.type).order_by(func.count().desc(), Merchant.type.asc())
    ).all()
    latest_merchants = db.scalars(
        select(Merchant).options(selectinload(Merchant.packages), selectinload(Merchant.images)).order_by(Merchant.created_at.desc()).limit(5)
    ).all()

    return DashboardSummary(
        total_merchants=total_merchants,
        active_merchants=active_merchants,
        total_insights=total_insights,
        total_admin_users=total_admin_users,
        merchant_count_by_category=[CountByBucket(key=row[0], count=row[1]) for row in category_rows],
        merchant_count_by_type=[CountByBucket(key=row[0], count=row[1]) for row in type_rows],
        latest_merchants=[serialize_merchant(item) for item in latest_merchants],
    )
