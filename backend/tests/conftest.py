from __future__ import annotations

import shutil

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, repo_root
from app.main import create_app


def make_settings(tmp_path, **overrides) -> Settings:
    config = tmp_path / "config"
    config.mkdir()
    root = repo_root()
    shutil.copy(root / "config" / "devices.example.yaml", config / "devices.example.yaml")
    shutil.copy(root / "config" / "features.example.yaml", config / "features.example.yaml")
    values = {
        "database_url": f"sqlite:///{tmp_path / 'mer.db'}",
        "devices_config": str(config / "devices.example.yaml"),
        "features_config": str(config / "features.example.yaml"),
        "reports_dir": str(tmp_path / "reports"),
        "backup_dir": str(tmp_path / "backups"),
        "config_dir": str(config),
        "secret_key": "test-secret",
        "dev_seed": True,
        "fast_retry": True,
        "allow_dev_secret": True,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture
def settings(tmp_path):
    return make_settings(tmp_path)


@pytest.fixture
def client(settings):
    application = create_app(settings)
    with TestClient(application) as test_client:
        yield test_client


def auth_header(client: TestClient, username: str = "admin", password: str = "Admin123!") -> dict:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
