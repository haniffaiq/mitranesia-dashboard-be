from __future__ import annotations

from tests.test_insights import insight_payload
from tests.test_merchants import merchant_payload


def test_dashboard_summary(client, auth_headers):
    merchant_response = client.post("/api/dashboard/merchants", json=merchant_payload(), headers=auth_headers)
    assert merchant_response.status_code == 201, merchant_response.text
    insight_response = client.post("/api/dashboard/insights", json=insight_payload("published"), headers=auth_headers)
    assert insight_response.status_code == 201, insight_response.text

    response = client.get("/api/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200, response.text
    summary = response.json()["data"]
    assert summary["total_merchants"] == 1
    assert summary["active_merchants"] == 1
    assert summary["total_insights"] == 1
    assert summary["total_admin_users"] == 1
    assert summary["merchant_count_by_category"][0]["key"] == "Cleaning Service"
    assert summary["latest_merchants"][0]["slug"] == "soc-clean"
