from __future__ import annotations

IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnXlRsAAAAASUVORK5CYII="


def carousel_payload():
    return {
        "title": "Bisnis Autopilot",
        "image_url": "https://example.com/carousel.jpg",
        "tag": "Trending",
        "icon": "trending-up",
        "highlight": "100% Keuntungan",
        "description": "Slide carousel test.",
        "color": "from-primary/95 via-primary/60",
        "cta_label": "Pelajari Lebih Lanjut",
        "cta_href": "/merchants",
        "sort_order": 1,
        "is_active": True,
    }


def test_dashboard_carousel_crud_and_client_listing(client, auth_headers):
    create_response = client.post("/api/dashboard/carousels", json=carousel_payload(), headers=auth_headers)
    assert create_response.status_code == 201, create_response.text
    carousel = create_response.json()["data"]

    list_response = client.get("/api/dashboard/carousels", headers=auth_headers)
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["meta"]["total"] == 1

    update_response = client.put(
        f"/api/dashboard/carousels/{carousel['id']}",
        json={**carousel_payload(), "title": "Bisnis Autopilot Updated", "sort_order": 2},
        headers=auth_headers,
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["data"]["title"] == "Bisnis Autopilot Updated"

    client_response = client.get("/api/client/carousels")
    assert client_response.status_code == 200, client_response.text
    assert client_response.json()[0]["title"] == "Bisnis Autopilot Updated"

    home_response = client.get("/api/client/home")
    assert home_response.status_code == 200, home_response.text
    assert home_response.json()["carouselSlides"][0]["title"] == "Bisnis Autopilot Updated"

    status_response = client.patch(
        f"/api/dashboard/carousels/{carousel['id']}/status",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["data"]["is_active"] is False


def test_dashboard_carousel_accepts_base64_image(client, auth_headers):
    payload = carousel_payload()
    payload["image_url"] = None
    payload["image_base64"] = IMAGE_BASE64

    response = client.post("/api/dashboard/carousels", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    carousel = response.json()["data"]
    assert carousel["image_url"].startswith("/uploads/cms/carousels/")
    assert carousel["image_base64"] in (None, "")

    client_response = client.get("/api/client/carousels")
    assert client_response.status_code == 200, client_response.text
    assert client_response.json()[0]["image"].startswith("/uploads/cms/carousels/")
