from __future__ import annotations

from app.core.security import hash_password
from app.models.admin_user import AdminUser


def test_editor_cannot_manage_admin_users(client, db_session):
    editor = AdminUser(username="editor1", password_hash=hash_password("editorpass123"), role="editor", is_active=True)
    db_session.add(editor)
    db_session.commit()

    login = client.post("/api/dashboard/auth/login", json={"username": "editor1", "password": "editorpass123"})
    token = login.json()["access_token"]

    response = client.get("/api/dashboard/admin-users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
