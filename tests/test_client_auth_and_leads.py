from __future__ import annotations


def register_payload():
    return {
        "full_name": "Hanif Test",
        "email": "hanif@example.com",
        "phone": "081234567890",
        "password": "password123",
    }


def create_merchant(client, auth_headers):
    response = client.post(
        "/api/dashboard/merchants",
        json={
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
                {"name": "Starter", "price": 2500000, "description": "Starter package", "sort_order": 1},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_client_register_login_and_me(client):
    register_response = client.post("/api/client/auth/register", json=register_payload())
    assert register_response.status_code == 201, register_response.text
    body = register_response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "hanif@example.com"

    login_response = client.post(
        "/api/client/auth/login",
        json={"email": "hanif@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    me_response = client.get("/api/client/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["data"]["full_name"] == "Hanif Test"


def test_client_create_inquiry_and_application(client, auth_headers):
    merchant = create_merchant(client, auth_headers)
    register_response = client.post("/api/client/auth/register", json=register_payload())
    token = register_response.json()["access_token"]
    client_headers = {"Authorization": f"Bearer {token}"}

    inquiry_response = client.post(
        "/api/client/merchant-inquiries",
        json={
            "merchant_id": merchant["id"],
            "package_name": merchant["packages"][0]["name"],
            "inquiry_type": "buy",
            "message": "Saya tertarik dengan paket ini.",
        },
        headers=client_headers,
    )
    assert inquiry_response.status_code == 201, inquiry_response.text
    assert inquiry_response.json()["data"]["inquiry_type"] == "buy"

    application_response = client.post(
        "/api/client/merchant-applications",
        json={
            "contact_name": "Hanif Test",
            "business_name": "Kopi Hanif",
            "email": "hanif@example.com",
            "phone": "081234567890",
            "category": "Food & Beverage",
            "city": "Jakarta",
            "message": "Saya ingin listing bisnis saya di Mitranesia.",
        },
        headers=client_headers,
    )
    assert application_response.status_code == 201, application_response.text
    assert application_response.json()["data"]["business_name"] == "Kopi Hanif"
