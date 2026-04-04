from __future__ import annotations


def insight_payload(status: str = "draft"):
    return {
        "title": "Tren Bisnis Franchise 2026",
        "slug": "tren-bisnis-franchise-2026",
        "category": "Bisnis",
        "author": "Tim Mitranesia",
        "image": "https://example.com/insight.jpg",
        "excerpt": "Ringkasan insight.",
        "read_time": "5 min baca",
        "content": ["Paragraf 1", "Paragraf 2"],
        "status": status,
    }


def test_insight_publish_flow(client, auth_headers):
    create_response = client.post("/api/dashboard/insights", json=insight_payload(), headers=auth_headers)
    assert create_response.status_code == 201, create_response.text
    article = create_response.json()["data"]
    assert article["published_at"] is None

    publish_response = client.patch(
        f"/api/dashboard/insights/{article['id']}/status",
        json={"status": "published"},
        headers=auth_headers,
    )
    assert publish_response.status_code == 200, publish_response.text
    published = publish_response.json()["data"]
    assert published["status"] == "published"
    assert published["published_at"] is not None
