from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, validate_settings
from app.main import app


def test_placeholder_secret_rejected() -> None:
    s = Settings.model_construct(
        mer_secret="change-me-dev-only", mer_env="dev", mer_allow_dev_auth=False
    )
    with pytest.raises(RuntimeError):
        validate_settings(s)


def test_features_reads_live_state() -> None:
    with TestClient(app) as c:
        import app.main_state as state

        tok = c.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"}).json()[
            "access_token"
        ]
        h = {"Authorization": f"Bearer {tok}"}
        state.features.e_sign = True
        try:
            feat = c.get("/api/v1/settings/features", headers=h).json()
            limits = c.get("/api/v1/settings/limits", headers=h).json()
            ready = c.get("/ready").json()
            assert feat["e_sign"] is True
            assert limits["e_sign"] is True
            assert ready["e_sign"] is True
        finally:
            state.features.e_sign = False
