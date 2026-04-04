from __future__ import annotations

from app.schemas.common import APIModel
from app.schemas.merchant import MerchantRead


class CountByBucket(APIModel):
    key: str
    count: int


class DashboardSummary(APIModel):
    total_merchants: int
    active_merchants: int
    total_insights: int
    total_admin_users: int
    merchant_count_by_category: list[CountByBucket]
    merchant_count_by_type: list[CountByBucket]
    latest_merchants: list[MerchantRead]
