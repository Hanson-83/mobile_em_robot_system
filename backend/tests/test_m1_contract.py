"""M1：适配契约、Fake、Gateway/OpenAPI、鉴权。"""

from __future__ import annotations

import json
import time

import pytest

from app.adapters.factory import AdapterFactory
from app.adapters.fake_amr import AmrFake
from app.adapters.fake_elevator import ElevatorFake
from app.core.errors import AppError
from tests.conftest import auth_header


def test_openapi_groups_and_health(client):
    health = client.get("/health")
    assert health.status_code == 200
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["db"] is True
    assert ready.json()["degraded"] is False
    denied = client.get("/api/v1/tasks")
    assert denied.status_code == 401
    assert denied.json()["code"] == "AUTH_REQUIRED"
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    for path in [
        "/api/v1/auth/login",
        "/api/v1/tasks",
        "/api/v1/tasks/{task_id}/cancel",
        "/api/v1/points",
        "/api/v1/measurements",
        "/api/v1/alarms",
        "/api/v1/alarms/export",
        "/api/v1/reports",
        "/api/v1/approvals",
        "/api/v1/settings/limits",
        "/api/v1/users",
        "/api/v1/robots",
        "/api/v1/maps",
    ]:
        assert path in paths, path
    tags = {tag for item in paths.values() for operation in item.values() if isinstance(operation, dict) for tag in operation.get("tags", [])}
    assert {"operations", "data", "settings"} <= tags
    assert schema["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
    assert schema["paths"]["/api/v1/tasks"]["get"]["security"] == [{"bearerAuth": []}]
    assert "401" in schema["paths"]["/api/v1/tasks"]["get"]["responses"]
    assert "429" in schema["paths"]["/api/v1/tasks"]["get"]["responses"]
    assert "/api/v1/ws" in paths


def test_default_esign_off_and_api_token(client, settings):
    headers = auth_header(client)
    features = client.get("/api/v1/settings/features", headers=headers).json()
    assert features["e_sign"] is False
    assert features["audit_trail"] is False
    assert features["elevator_skills"] is True
    robots = client.get("/api/v1/robots", headers={"Authorization": f"Bearer {settings.dev_api_token}"})
    assert robots.status_code == 200
    assert {item["id"] for item in robots.json()["items"]} == {"robot-01", "robot-02"}


def test_factory_switches_fake_recorded_and_vendor(tmp_path):
    recording = tmp_path / "amr.json"
    recording.write_text(json.dumps({"status": {"battery_pct": 66, "pose": {"x": 3, "y": 4}}}), encoding="utf-8")
    registry = AdapterFactory().build(
        {
            "robots": [
                {"id": "r-fake", "adapter": "amr_fake"},
                {"id": "r-rec", "adapter": "amr_recorded", "recording": str(recording)},
                {"id": "r-vendor", "adapter": "amr_vendor_x"},
            ],
            "instruments": [
                {"id": "p1", "robot_id": "r-fake", "kind": "particle", "adapter": "particle_fake", "access_mode": "direct"}
            ],
            "elevators": [
                {"id": "e-fake", "adapter": "elevator_fake", "floors": [1, 2]},
                {"id": "e-vendor", "adapter": "elevator_vendor_x"},
            ],
        }
    )
    fake = registry.amr("r-fake")
    assert isinstance(fake, AmrFake)
    assert not hasattr(AmrFake, "call_elevator")
    recorded = registry.amr("r-rec")
    recorded.start()
    assert recorded.get_status().battery_pct == 66
    vendor = registry.amr("r-vendor")
    with pytest.raises(AppError, match="API"):
        vendor.connect()
    elevator = registry.elevator("e-fake")
    assert isinstance(elevator, ElevatorFake)
    elevator.start()
    elevator.call_elevator(2)
    elevator.enter_elevator()
    elevator.exit_elevator({"floor": 2})
    assert elevator.history == ["call:2", "enter", "exit:2"]
    assert registry.instrument("p1").access_mode == "direct"


def test_rbac_forbidden(client):
    headers = auth_header(client, "viewer", "Viewer123!")
    response = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-01", "point_id": "point-a"})
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_heartbeat_timeout_and_reconnect():
    amr = AmrFake("hb-01")
    amr.configure_session(0.05)
    amr.connect()
    assert amr.health().ok is True
    time.sleep(0.06)
    assert amr.health().detail == "heartbeat timeout"
    amr.heartbeat()
    assert amr.health().ok is True


def test_random_bearer_shares_ip_bucket(tmp_path):
    from fastapi.testclient import TestClient

    from app.main import create_app
    from tests.conftest import make_settings

    application = create_app(make_settings(tmp_path, rate_limit_per_min=2))
    with TestClient(application) as client:
        assert client.get("/api/v1/maps", headers={"Authorization": "Bearer aaa"}).status_code == 401
        assert client.get("/api/v1/maps", headers={"Authorization": "Bearer bbb"}).status_code == 401
        blocked = client.get("/api/v1/maps", headers={"Authorization": "Bearer ccc"})
        assert blocked.status_code == 429
