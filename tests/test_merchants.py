from __future__ import annotations

IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnXlRsAAAAASUVORK5CYII="


def merchant_payload():
    return {
        "name": "Soc Clean",
        "slug": "soc-clean",
        "category": "Cleaning Service",
        "type": "Semi-Autopilot",
        "logo_url": "https://example.com/logo.png",
        "bep_months": 8,
        "rating": 4.8,
        "is_active": True,
        "is_top_merchant": False,
        "description": "Initial merchant",
        "packages": [
            {"name": "Starter", "price": 2500000, "description": "Starter package", "sort_order": 0},
            {"name": "Premium", "price": 15000000, "description": "Premium package", "sort_order": 1},
        ],
    }


def test_create_and_update_merchant_packages(client, auth_headers):
    create_response = client.post("/api/dashboard/merchants", json=merchant_payload(), headers=auth_headers)
    assert create_response.status_code == 201, create_response.text
    merchant = create_response.json()["data"]
    packages = merchant["packages"]
    assert len(packages) == 2

    update_payload = merchant_payload()
    update_payload["name"] = "Soc Clean Updated"
    update_payload["packages"] = [
        {
            "id": packages[0]["id"],
            "name": "Starter Updated",
            "price": 3000000,
            "description": "Updated starter",
            "sort_order": 0,
        },
        {
            "name": "Enterprise",
            "price": 20000000,
            "description": "New enterprise package",
            "sort_order": 1,
        },
    ]
    update_response = client.put(f"/api/dashboard/merchants/{merchant['id']}", json=update_payload, headers=auth_headers)
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()["data"]
    assert updated["name"] == "Soc Clean Updated"
    assert len(updated["packages"]) == 2
    assert {item["name"] for item in updated["packages"]} == {"Starter Updated", "Enterprise"}


def test_slug_uniqueness(client, auth_headers):
    first = client.post("/api/dashboard/merchants", json=merchant_payload(), headers=auth_headers)
    assert first.status_code == 201, first.text

    second_payload = merchant_payload()
    second_payload["name"] = "Soc Clean Clone"
    second = client.post("/api/dashboard/merchants", json=second_payload, headers=auth_headers)
    assert second.status_code == 422


def test_create_merchant_with_base64_logo(client, auth_headers):
    payload = merchant_payload()
    payload["logo_url"] = None
    payload["logo_base64"] = IMAGE_BASE64

    response = client.post("/api/dashboard/merchants", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    merchant = response.json()["data"]
    assert merchant["logo_url"] == ""
    assert merchant["logo_base64"] == IMAGE_BASE64
