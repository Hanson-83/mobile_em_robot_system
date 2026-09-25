from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_fake_task_with_elevator_smoke() -> None:
    with TestClient(app) as c:
        tok = c.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin"}
        ).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = c.post(
            "/api/v1/tasks",
            headers=h,
            json={
                "robot_id": "robot-01",
                "point_id": "P1",
                "elevator_id": "elev-01",
                "elevator_floor": 2,
            },
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["state"] == "Succeeded"
        assert body["elevator_trace"] == ["succeeded", "succeeded", "succeeded"]
        assert any("pc-01" == s["instrument_id"] for s in body["samples"])
        robots = c.get("/api/v1/robots", headers=h).json()
        assert robots[0]["id"] == "robot-01"
