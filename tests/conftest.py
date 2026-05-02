from __future__ import annotations

import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///./test_dashboard.db"
os.environ["CREATE_TABLES_ON_START"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-32-plus-bytes"
os.environ["DEFAULT_SUPERADMIN_USERNAME"] = "superadmin"
os.environ["DEFAULT_SUPERADMIN_PASSWORD"] = "superadmin123"
os.environ.setdefault("UPLOAD_ROOT", tempfile.mkdtemp(prefix="mitranesia-uploads-"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import Base
from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    Base.metadata.drop_all(bind=app.state.engine)
    Base.metadata.create_all(bind=app.state.engine)
    with Session(app.state.engine) as db:
        from app.services.bootstrap import seed_default_superadmin

        seed_default_superadmin(db, app.state.settings)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=app.state.engine)


@pytest.fixture
def superadmin_token(client: TestClient) -> str:
    response = client.post(
        "/api/dashboard/auth/login",
        json={"username": "superadmin", "password": "superadmin123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(superadmin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {superadmin_token}"}


@pytest.fixture
def db_session(client: TestClient):
    with Session(client.app.state.engine) as db:
        yield db
