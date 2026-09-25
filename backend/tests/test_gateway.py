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
    assert "/api/v1/ws/info" in paths
    assert "/api/v1/users" in paths
    assert "/api/v1/points/{point_id}" in paths


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


def test_rate_limited(client: TestClient, admin_token: str):
    client.app.state.rate_limiter.per_min = 2
    client.app.state.rate_limiter._hits.clear()
    headers = {"Authorization": f"Bearer {admin_token}"}
    assert client.get("/api/v1/tasks", headers=headers).status_code == 200
    assert client.get("/api/v1/tasks", headers=headers).status_code == 200
    res = client.get("/api/v1/tasks", headers=headers)
    assert res.status_code == 429
    assert res.json()["code"] == "RATE_LIMITED"
    assert res.json()["retryable"] is True


def test_point_delete_and_user_create(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/v1/points",
        headers=headers,
        json={"id": "P9", "name": "临时点", "map_id": "map-01", "pose": {"x": 0, "y": 0}},
    )
    assert created.status_code == 201
    deleted = client.delete("/api/v1/points/P9", headers=headers)
    assert deleted.status_code == 204
    user = client.post(
        "/api/v1/users",
        headers=headers,
        json={"username": "qa1", "password": "qa1-pass", "role": "viewer"},
    )
    assert user.status_code == 201
    names = {u["username"] for u in client.get("/api/v1/users", headers=headers).json()}
    assert "qa1" in names


def test_prod_rejects_weak_secrets(settings):
    from app.core.config import assert_runtime_secrets
    from app.main import create_app

    try:
        create_app(settings.model_copy(update={"env": "prod"}))
        raise AssertionError("默认密钥在 prod 应拒绝启动")
    except RuntimeError:
        pass
    only_jwt_default = settings.model_copy(
        update={
            "env": "prod",
            "jwt_secret": "dev-only-change-me",
            "bootstrap_admin_password": "Adm#9xQ2long",
            "bootstrap_operator_password": "Opr#9xQ2long",
            "bootstrap_viewer_password": "Vwr#9xQ2long",
        }
    )
    try:
        assert_runtime_secrets(only_jwt_default)
        raise AssertionError("默认 JWT 在 prod 应拒绝")
    except RuntimeError:
        pass
    short_jwt = settings.model_copy(
        update={
            "env": "prod",
            "jwt_secret": "short",
            "bootstrap_admin_password": "Adm#9xQ2long",
            "bootstrap_operator_password": "Opr#9xQ2long",
            "bootstrap_viewer_password": "Vwr#9xQ2long",
        }
    )
    try:
        assert_runtime_secrets(short_jwt)
        raise AssertionError("短 JWT 在 prod 应拒绝")
    except RuntimeError:
        pass
    strong = settings.model_copy(
        update={
            "env": "prod",
            "jwt_secret": "prod-secret-not-default",
            "bootstrap_admin_password": "Adm#9xQ2long",
            "bootstrap_operator_password": "Opr#9xQ2long",
            "bootstrap_viewer_password": "Vwr#9xQ2long",
        }
    )
    assert_runtime_secrets(strong)


def test_compose_requires_secrets():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "deploy/docker-compose.yml").read_text(
        encoding="utf-8"
    )
    assert "dev-only-change-me" not in text
    assert "${MER_JWT_SECRET:?set MER_JWT_SECRET}" in text


def test_point_patch_rejects_id_change(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.patch("/api/v1/points/P1", headers=headers, json={"id": "P-EVIL", "name": "改名"})
    assert res.status_code == 422
    ok = client.patch("/api/v1/points/P1", headers=headers, json={"name": "洁净走廊-1A"})
    assert ok.status_code == 200
    assert ok.json()["id"] == "P1"
    assert ok.json()["name"] == "洁净走廊-1A"
    bad_pose = client.patch(
        "/api/v1/points/P1",
        headers=headers,
        json={"pose": "not-a-pose"},
    )
    assert bad_pose.status_code == 422
    assert bad_pose.json()["code"] == "VALIDATION_ERROR"
