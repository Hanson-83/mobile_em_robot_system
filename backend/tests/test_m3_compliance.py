"""M3：审计、批准流、备份恢复、进程重启失败语义。"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app
from app.services.bootstrap import VIEWER
from tests.conftest import auth_header, make_settings


def test_audit_append_only(client):
    headers = auth_header(client)
    turned = client.patch("/api/v1/settings/features", headers=headers, json={"audit_trail": True})
    assert turned.status_code == 200
    client.post(
        "/api/v1/points",
        headers=headers,
        json={"id": "point-d", "map_id": "map-demo", "name": "D", "pose": {"x": 1, "y": 2, "theta": 0}, "limits": {}},
    )
    audits = client.get("/api/v1/audit", headers=headers).json()["items"]
    assert any(item["action"] == "point.upsert" and item["actor"] == "admin" for item in audits)
    removed = client.delete("/api/v1/audit", headers=headers)
    assert removed.status_code == 405
    viewer = auth_header(client, "viewer", "Viewer123!")
    assert client.get("/api/v1/audit", headers=viewer).status_code == 403


def test_approval_flow(client):
    headers = auth_header(client)
    assert client.get("/api/v1/settings/features", headers=headers).json()["e_sign"] is False
    direct = client.patch(
        "/api/v1/settings/limits",
        headers=headers,
        json={"point_id": "point-b", "limits": {"temp_c": {"min": 10, "max": 30}}},
    )
    assert direct.status_code == 200
    assert direct.json()["limits"]["temp_c"]["max"] == 30
    client.patch("/api/v1/settings/features", headers=headers, json={"e_sign": True})
    blocked = client.patch(
        "/api/v1/settings/limits",
        headers=headers,
        json={"point_id": "point-b", "limits": {"temp_c": {"min": 1, "max": 2}}},
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "APPROVAL_REQUIRED"
    approval_id = blocked.json()["details"]["approval_id"]
    assert client.get("/api/v1/settings/limits", headers=headers, params={"point_id": "point-b"}).json()["limits"]["temp_c"]["max"] == 30
    rejected = client.post(
        f"/api/v1/approvals/{approval_id}/reject",
        headers=headers,
        json={"password": "Admin123!", "meaning": "不同意"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["state"] == "Rejected"
    assert client.get("/api/v1/settings/limits", headers=headers, params={"point_id": "point-b"}).json()["limits"]["temp_c"]["max"] == 30
    blocked = client.patch(
        "/api/v1/settings/limits",
        headers=headers,
        json={"point_id": "point-b", "limits": {"temp_c": {"min": 19, "max": 24}}},
    )
    approval_id = blocked.json()["details"]["approval_id"]
    approved = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers=headers,
        json={"password": "Admin123!", "meaning": "确认限值"},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "Approved"
    assert client.get("/api/v1/settings/limits", headers=headers, params={"point_id": "point-b"}).json()["limits"]["temp_c"]["max"] == 24


def test_approval_expired(tmp_path):
    application = create_app(make_settings(tmp_path, approval_ttl_hours=0))
    with TestClient(application) as client:
        headers = auth_header(client)
        client.patch("/api/v1/settings/features", headers=headers, json={"e_sign": True})
        blocked = client.patch(
            "/api/v1/settings/limits",
            headers=headers,
            json={"point_id": "point-a", "limits": {"temp_c": {"max": 21}}},
        )
        approval_id = blocked.json()["details"]["approval_id"]
        decision = client.post(
            f"/api/v1/approvals/{approval_id}/approve",
            headers=headers,
            json={"password": "Admin123!", "meaning": "过期"},
        )
        assert decision.status_code == 409
        limits = client.get("/api/v1/settings/limits", headers=headers, params={"point_id": "point-a"}).json()["limits"]
        assert limits["temp_c"]["max"] == 26


def test_backup_restore_roundtrip(client):
    headers = auth_header(client)
    client.post(
        "/api/v1/points",
        headers=headers,
        json={"id": "point-bak", "map_id": "map-demo", "name": "备份点", "pose": {"x": 5, "y": 5, "theta": 0}, "limits": {"temp_c": {"max": 25}}},
    )
    backup = client.post("/api/v1/backups", headers=headers)
    assert backup.status_code == 200, backup.text
    assert "sqlite" in backup.json()["scope"]
    assert client.delete("/api/v1/points/point-bak", headers=headers).status_code == 200
    assert client.get("/api/v1/settings/limits", headers=headers, params={"point_id": "point-bak"}).status_code == 404
    restored = client.post(f"/api/v1/backups/{backup.json()['id']}/restore", headers=headers)
    assert restored.status_code == 200, restored.text
    limits = client.get("/api/v1/settings/limits", headers=headers, params={"point_id": "point-bak"})
    assert limits.status_code == 200
    assert limits.json()["limits"]["temp_c"]["max"] == 25


def test_process_restart_marks_running_failed(tmp_path):
    settings = make_settings(tmp_path)
    with TestClient(create_app(settings)) as client:
        headers = auth_header(client)
        created = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-01", "point_id": "point-a"})
        client.post("/api/v1/scheduler/dispatch", headers=headers)
        task_id = created.json()["id"]
    with TestClient(create_app(settings)) as client:
        headers = auth_header(client)
        task = next(item for item in client.get("/api/v1/tasks", headers=headers).json()["items"] if item["id"] == task_id)
        assert task["status"] == "Failed"
        assert task["error_code"] == "PROCESS_RESTART"


def test_rate_limit(tmp_path):
    application = create_app(make_settings(tmp_path, rate_limit_per_min=2))
    with TestClient(application) as client:
        headers = auth_header(client)
        assert client.get("/api/v1/maps", headers=headers).status_code == 200
        assert client.get("/api/v1/maps", headers=headers).status_code == 200
        blocked = client.get("/api/v1/maps", headers=headers)
        assert blocked.status_code == 429
        assert blocked.json()["code"] == "RATE_LIMITED"
        assert blocked.json()["retryable"] is True


def test_group_role_grants_permission(client):
    headers = auth_header(client)
    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={"username": "extra", "password": "Extra123!", "roles": ["viewer"]},
    )
    assert created.status_code == 200, created.text
    groups = client.get("/api/v1/groups", headers=headers).json()["items"]
    operators = next(item for item in groups if item["name"] == "operators")
    patched = client.patch(
        f"/api/v1/groups/{operators['id']}",
        headers=headers,
        json={"user_ids": [*operators["user_ids"], created.json()["id"]]},
    )
    assert patched.status_code == 200, patched.text
    extra = auth_header(client, "extra", "Extra123!")
    task = client.post("/api/v1/tasks", headers=extra, json={"robot_id": "robot-01", "point_id": "point-a"})
    assert task.status_code == 200, task.text


def test_role_permission_is_configurable(client):
    headers = auth_header(client)
    updated = client.patch(
        "/api/v1/roles/viewer",
        headers=headers,
        json={"permissions": [*VIEWER, "operations.task.write"]},
    )
    assert updated.status_code == 200, updated.text
    viewer = auth_header(client, "viewer", "Viewer123!")
    task = client.post("/api/v1/tasks", headers=viewer, json={"robot_id": "robot-01", "point_id": "point-b"})
    assert task.status_code == 200, task.text


def test_report_approve_and_audit_switch_are_recorded(client):
    headers = auth_header(client)
    client.patch("/api/v1/settings/features", headers=headers, json={"audit_trail": True})
    created = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"robot_id": "robot-01", "skills": [{"type": "navigate_to", "params": {"point_id": "point-a"}}]},
    )
    client.post("/api/v1/scheduler/drain", headers=headers)
    report = next(item for item in client.get("/api/v1/reports", headers=headers).json()["items"] if item["task_ref"] == created.json()["id"])
    approved = client.post(f"/api/v1/reports/{report['id']}/approve", headers=headers)
    assert approved.status_code == 200, approved.text
    client.patch("/api/v1/settings/features", headers=headers, json={"audit_trail": False})
    audits = client.get("/api/v1/audit", headers=headers).json()["items"]
    assert any(item["action"] == "report.approve" for item in audits)
    closing = [item for item in audits if item["action"] == "features.update" and item["after"].get("audit_trail") is False]
    assert closing


def test_auto_backup_restores_active_yaml(tmp_path):
    settings = make_settings(tmp_path)
    custom = Path(tmp_path / "custom" / "devices.yaml")
    custom.parent.mkdir()
    custom.write_text(Path(settings.devices_config).read_text(encoding="utf-8"), encoding="utf-8")
    settings.devices_config = str(custom)
    with TestClient(create_app(settings)) as client:
        headers = auth_header(client)
        backups = client.get("/api/v1/backups", headers=headers).json()["items"]
        assert backups
        custom.write_text("changed: true\n", encoding="utf-8")
        oldest = backups[-1]
        restored = client.post(f"/api/v1/backups/{oldest['id']}/restore", headers=headers)
        assert restored.status_code == 200, restored.text
        assert "changed" not in custom.read_text(encoding="utf-8")
        assert "robots" in custom.read_text(encoding="utf-8") or "robot" in custom.read_text(encoding="utf-8")


def test_audit_table_rejects_update(client):
    headers = auth_header(client)
    client.patch("/api/v1/settings/features", headers=headers, json={"audit_trail": True})
    client.post(
        "/api/v1/points",
        headers=headers,
        json={"id": "point-e", "map_id": "map-demo", "name": "E", "pose": {"x": 1, "y": 1, "theta": 0}, "limits": {}},
    )
    engine = client.app.state.runtime.engine
    with pytest.raises(Exception, match="audit append-only"):
        with engine.begin() as connection:
            connection.execute(text("UPDATE audit_events SET actor = 'hacker'"))
