from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def _token(c: TestClient, user: str = "admin", password: str | None = None) -> str:
    r = c.post("/api/v1/auth/login", json={"username": user, "password": password or user})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_health_ready_and_openapi_groups() -> None:
    with _client() as c:
        assert c.get("/health").json()["status"] == "ok"
        ready = c.get("/ready").json()
        assert ready["status"] == "ready"
        assert ready["e_sign"] is False
        types = {a["type"] for a in ready["adapters"]}
        assert "amr_fake" in types
        assert "elevator_fake" in types
        spec = c.get("/openapi.json").json()
        groups = spec["info"]["x-mer-groups"]
        assert set(groups) == {"operations", "data", "settings"}
        paths = spec["paths"]
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/tasks" in paths
        assert "/api/v1/robots" in paths
        assert "/api/v1/reports" in paths
        assert "/api/v1/approvals" in paths
        assert "/api/v1/users" in paths
        assert "/api/v1/alarms/{alarm_id}/ack" in paths
        assert "post" in paths["/api/v1/points"]
        assert "patch" in paths["/api/v1/settings/limits"]
        assert "post" in paths["/api/v1/users"]
        assert "/api/v1/tasks/{id}/cancel" in paths
        assert "Error" in spec["components"]["schemas"]
        err = spec["components"]["schemas"]["Error"]
        for field in ("code", "message", "retryable"):
            assert field in err["required"]

        from pathlib import Path

        import yaml

        sketch = yaml.safe_load((Path(__file__).resolve().parents[1] / "app/api/openapi_v1.sketch.yaml").read_text())
        for p in (
            "/api/v1/auth/login",
            "/api/v1/tasks",
            "/api/v1/tasks/{id}/cancel",
            "/api/v1/points",
            "/api/v1/reports",
            "/api/v1/approvals",
            "/api/v1/users",
            "/api/v1/settings/limits",
        ):
            assert p in sketch["paths"], p
            assert p in paths, p
        assert "Error" in sketch["components"]["schemas"]


def test_auth_required() -> None:
    with _client() as c:
        r = c.get("/api/v1/robots")
        assert r.status_code == 401
        assert r.json()["code"] == "AUTH_REQUIRED"


def test_rbac_operator_forbidden_settings() -> None:
    with _client() as c:
        tok = _token(c, "operator")
        r = c.get("/api/v1/settings/limits", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403
        assert r.json()["code"] == "FORBIDDEN"


def test_login_bad_password() -> None:
    with _client() as c:
        r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401
