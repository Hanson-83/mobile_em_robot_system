from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_and_ready(client: TestClient):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ok"
    assert "robot-01" in ready.json()["adapters"]
    assert "elev-01" in ready.json()["adapters"]


def test_openapi_groups(client: TestClient):
    spec = client.get("/openapi.json").json()
    names = {t["name"] for t in spec["tags"]}
    assert names == {"operations", "data", "settings"}
    paths = spec["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/tasks" in paths
    assert "/api/v1/measurements" in paths
    assert "/api/v1/points" in paths
    assert "/api/v1/settings/limits" in paths
    assert "/api/v1/ws" in paths


def test_auth_required(client: TestClient):
    res = client.get("/api/v1/tasks")
    assert res.status_code == 401
    body = res.json()
    assert body["code"] == "AUTH_REQUIRED"
    assert body["retryable"] is False


def test_login_and_rbac(client: TestClient, admin_token: str, viewer_token: str):
    created = client.post(
        "/api/v1/tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "巡检A", "robot_id": "robot-01", "skills": [{"type": "navigate_to"}]},
    )
    assert created.status_code == 201
    forbidden = client.post(
        "/api/v1/tasks",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"name": "越权", "robot_id": "robot-01"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "FORBIDDEN"


def test_points_and_robots(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    points = client.get("/api/v1/points", headers=headers)
    assert points.status_code == 200
    robots = client.get("/api/v1/robots", headers=headers)
    assert robots.status_code == 200
    assert robots.json()[0]["robot_id"] == "robot-01"
    features = client.get("/api/v1/settings/features", headers=headers)
    assert features.status_code == 200
    assert features.json()["e_sign"] is False


def test_measurement_idempotency(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "device_id": "pc-01",
        "sample_id": "s1",
        "metric": "particle.0.5um",
        "value": 88,
        "unit": "count",
        "ts": "2026-09-25T00:00:00+00:00",
        "client_request_id": "req-1",
    }
    first = client.post("/api/v1/measurements", headers=headers, json=payload)
    second = client.post("/api/v1/measurements", headers=headers, json=payload)
    assert first.status_code == 200
    assert second.json()["code"] == "IDEMPOTENCY_REPLAY"
    listed = client.get("/api/v1/measurements", headers=headers).json()
    assert len(listed) == 1


def test_e_sign_blocks_limit_change(settings):
    from app.main import create_app

    settings_on = settings.model_copy()
    app = create_app(settings_on)
    app.state.features.e_sign = True
    with TestClient(app) as client:
        token = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin"}
        ).json()["access_token"]
        res = client.patch(
            "/api/v1/settings/limits",
            headers={"Authorization": f"Bearer {token}"},
            json={"limits": {"particle.0.5um": 100.0}},
        )
        assert res.status_code == 409
        assert res.json()["code"] == "APPROVAL_REQUIRED"
