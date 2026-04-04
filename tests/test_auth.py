from __future__ import annotations


def test_login_success(client):
    response = client.post("/api/dashboard/auth/login", json={"username": "superadmin", "password": "superadmin123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "superadmin"


def test_login_failure(client):
    response = client.post("/api/dashboard/auth/login", json={"username": "superadmin", "password": "wrongpass123"})
    assert response.status_code == 401
