from __future__ import annotations

import json
import os

from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def _token(c: TestClient, user: str = "admin", password: str | None = None) -> str:
    r = c.post("/api/v1/auth/login", json={"username": user, "password": password or user})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_api_version_stable() -> None:
    with _client() as c:
        ver = c.get("/api/v1/version").json()
        assert ver["api"] == "1.0.0"
        assert ver["openapi_status"] == "stable"
        assert "integrations" in ver["groups"]
        assert ver["mes"]["version"] == "1.0.0"
        assert "desktop_client" in ver["deferred"]
        spec = c.get("/openapi.json").json()
        assert spec["info"]["version"] == "1.0.0"
        assert spec["info"]["x-mer-openapi-status"] == "stable"
        assert set(spec["info"]["x-mer-groups"]) == {
            "operations",
            "data",
            "settings",
            "integrations",
        }


def test_stable_catalog_paths_present() -> None:
    from pathlib import Path

    import yaml

    stable = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "app/api/openapi_v1.stable.yaml").read_text()
    )
    assert stable["info"]["version"] == "1.0.0"
    # FastAPI 不把 WebSocket 写入 openapi paths；stable 单独声明
    stable_only_allowlist = {"/api/v1/ws"}
    http_methods = {"get", "post", "put", "patch", "delete"}
    with _client() as c:
        runtime = c.get("/openapi.json").json()["paths"]
        stable_paths = set(stable["paths"]) - stable_only_allowlist
        runtime_paths = set(runtime)
        assert stable_paths == runtime_paths, (
            f"only_stable={sorted(stable_paths - runtime_paths)} "
            f"only_runtime={sorted(runtime_paths - stable_paths)}"
        )
        for p in runtime_paths:
            stable_m = {m for m in stable["paths"][p] if m in http_methods}
            runtime_m = {m for m in runtime[p] if m in http_methods}
            assert stable_m == runtime_m, f"{p}: stable={stable_m} runtime={runtime_m}"
        assert "/api/v1/ws" in stable["paths"]
        assert "/api/v1/admin/backup" in runtime
        assert "/api/v1/approvals/{approval_id}/decide" in runtime


def test_mes_task_lifecycle_and_realtime() -> None:
    with _client() as c:
        tok = _token(c)
        h = {"Authorization": f"Bearer {tok}"}
        cat = c.get("/api/v1/integrations/mes/catalog", headers=h).json()
        assert cat["integration"] == "mes_scada_dcs"
        assert "task.create" in cat["scope"]
        assert "幂等" in cat.get("idempotency", "")

        created = c.post(
            "/api/v1/integrations/mes/tasks",
            headers=h,
            json={
                "robot_id": "robot-01",
                "point_id": "P1",
                "auto_start": False,
                "client_request_id": "mes-req-001",
            },
        )
        assert created.status_code == 200, created.text
        task = created.json()
        assert task["state"] in {"Created", "Queued"}
        assert task["client_request_id"] == "mes-req-001"
        tid = task["id"]

        replay = c.post(
            "/api/v1/integrations/mes/tasks",
            headers=h,
            json={
                "robot_id": "robot-01",
                "point_id": "P1",
                "auto_start": False,
                "client_request_id": "mes-req-001",
            },
        )
        assert replay.status_code == 200, replay.text
        assert replay.json()["id"] == tid

        detail = c.get(f"/api/v1/integrations/mes/tasks/{tid}", headers=h)
        assert detail.status_code == 200
        assert detail.json()["id"] == tid

        stopped = c.post(f"/api/v1/integrations/mes/tasks/{tid}/stop", headers=h)
        assert stopped.status_code == 200, stopped.text
        assert stopped.json()["state"] == "Cancelled"

        started = c.post(
            "/api/v1/integrations/mes/tasks",
            headers=h,
            json={"robot_id": "robot-01", "point_id": "P1", "auto_start": True},
        )
        assert started.status_code == 200, started.text
        assert started.json()["state"] in {"Succeeded", "Failed", "Running", "Dispatched", "Queued"}

        rt = c.get("/api/v1/integrations/mes/realtime", headers=h)
        assert rt.status_code == 200
        body = rt.json()
        assert "robots" in body and "tasks" in body and "alarms" in body
        assert any(r["id"] == "robot-01" for r in body["robots"])
        web_rt = c.get("/api/v1/realtime", headers=h)
        assert web_rt.status_code == 200
        assert set(web_rt.json().keys()) == set(body.keys())


def test_api_token_auth() -> None:
    os.environ["MER_API_TOKENS_JSON"] = json.dumps(
        {
            "mes-token-demo": {
                "client_id": "mes-line-a",
                "roles": ["api_client"],
                "perms": [
                    "operations.task.read",
                    "operations.task.write",
                    "data.measurement.read",
                ],
            }
        }
    )
    try:
        with _client() as c:
            h = {"Authorization": "Bearer mes-token-demo"}
            r = c.get("/api/v1/integrations/mes/catalog", headers=h)
            assert r.status_code == 200, r.text
            bad = c.get("/api/v1/integrations/mes/catalog", headers={"Authorization": "Bearer wrong"})
            assert bad.status_code == 401
    finally:
        os.environ.pop("MER_API_TOKENS_JSON", None)
