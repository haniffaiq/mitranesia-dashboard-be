from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.insight_article import InsightArticle
from app.models.merchant import Merchant
from app.models.merchant_package import MerchantPackage

IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnXlRsAAAAASUVORK5CYII="


def seed_client_data(db_session):
    merchant = Merchant(
        id=uuid4(),
        name="Soc Clean",
        slug="soc-clean",
        category="Cleaning Service",
        type="Semi-Autopilot",
        logo_url=None,
        logo_base64=IMAGE_BASE64,
        bep_months=8,
        rating=4.7,
        is_active=True,
        is_top_merchant=True,
        description="Merchant test",
        packages=[
            MerchantPackage(name="Starter", price=2500000, description="Starter package", sort_order=1),
            MerchantPackage(name="Premium", price=15000000, description="Premium package", sort_order=2),
        ],
    )
    insight = InsightArticle(
        id=uuid4(),
        title="Tren Bisnis Franchise 2025",
        slug="tren-bisnis-franchise-2025",
        category="Bisnis",
        author="Tim Mitranesia",
        image=None,
        image_base64=IMAGE_BASE64,
        excerpt="Ringkasan insight.",
        read_time="5 min baca",
        content=["Paragraf 1", "Paragraf 2"],
        status="published",
        published_at=datetime(2025, 12, 18, 12, 0, 0, tzinfo=timezone.utc),
    )
    db_session.add(merchant)
    db_session.add(insight)
    db_session.commit()
    return merchant, insight


def test_client_home_and_filters(client, db_session):
    seed_client_data(db_session)

    home_response = client.get("/api/client/home")
    assert home_response.status_code == 200, home_response.text
    home = home_response.json()
    assert len(home["topMerchants"]) == 1
    assert home["topMerchants"][0]["logoUrl"] == IMAGE_BASE64
    assert home["featuredInsight"]["slug"] == "tren-bisnis-franchise-2025"
    assert home["featuredInsight"]["image"] == IMAGE_BASE64
    assert home["merchantFilters"]["categories"] == ["Cleaning Service"]

    filters_response = client.get("/api/client/merchants/filters")
    assert filters_response.status_code == 200, filters_response.text
    filters = filters_response.json()
    assert filters["minPrice"] == 2500000
    assert filters["maxPrice"] == 15000000


def test_client_merchant_list_and_detail(client, db_session):
    merchant, _ = seed_client_data(db_session)

    list_response = client.get("/api/client/merchants", params={"search": "soc", "sort_by": "min_price"})
    assert list_response.status_code == 200, list_response.text
    payload = list_response.json()
    assert payload["meta"]["total"] == 1
    assert payload["data"][0]["slug"] == "soc-clean"
    assert payload["data"][0]["minPrice"] == 2500000

    detail_by_id = client.get(f"/api/client/merchants/{merchant.id}")
    assert detail_by_id.status_code == 200, detail_by_id.text
    assert detail_by_id.json()["packages"][0]["name"] == "Starter"

    detail_by_slug = client.get("/api/client/merchants/soc-clean")
    assert detail_by_slug.status_code == 200, detail_by_slug.text
    assert detail_by_slug.json()["name"] == "Soc Clean"


def test_client_insight_list_and_detail(client, db_session):
    _, insight = seed_client_data(db_session)

    list_response = client.get("/api/client/insights")
    assert list_response.status_code == 200, list_response.text
    payload = list_response.json()
    assert len(payload) == 1
    assert payload[0]["date"] == "18 Des 2025"

    categories_response = client.get("/api/client/insights/categories")
    assert categories_response.status_code == 200, categories_response.text
    assert categories_response.json()["categories"] == ["Bisnis"]

    detail_by_id = client.get(f"/api/client/insights/{insight.id}")
    assert detail_by_id.status_code == 200, detail_by_id.text
    assert detail_by_id.json()["slug"] == "tren-bisnis-franchise-2025"

    detail_by_slug = client.get("/api/client/insights/tren-bisnis-franchise-2025")
    assert detail_by_slug.status_code == 200, detail_by_slug.text
    assert detail_by_slug.json()["title"] == "Tren Bisnis Franchise 2025"
