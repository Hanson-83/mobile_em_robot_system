from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def settings() -> Settings:
    return Settings(
        repo_root=REPO_ROOT,
        devices_path=Path("config/devices.example.yaml"),
        features_path=Path("config/features.example.yaml"),
        jwt_secret="test-secret",
        bootstrap_admin_password="admin",
        bootstrap_operator_password="operator",
    )


@pytest.fixture
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client: TestClient) -> str:
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def viewer_token(client: TestClient) -> str:
    res = client.post("/api/v1/auth/login", json={"username": "viewer", "password": "viewer"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]
