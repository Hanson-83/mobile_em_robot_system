from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.main_state as state
from app.core.errors import DomainError
from app.domain.task_fsm import assert_transition
from app.main import app


def _auth(c: TestClient) -> dict[str, str]:
    tok = c.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {tok}"}


def test_fsm_rejects_terminal_restart() -> None:
    with pytest.raises(DomainError):
        assert_transition("Succeeded", "Running")


def test_queue_then_start() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.mutex.acquire("point", "P1", holder="blocker", on_conflict="fail")
        queued = c.post(
            "/api/v1/tasks",
            headers=h,
            json={"robot_id": "robot-01", "point_id": "P1", "auto_start": True},
        ).json()
        assert queued["state"] == "Queued"
        assert queued["queue_reason"] == "point"
        state.mutex.release("point", "P1", holder="blocker")
        started = c.post(f"/api/v1/tasks/{queued['id']}/start", headers=h)
        assert started.status_code == 200, started.text
        assert started.json()["state"] == "Succeeded"


def test_estop_fails_task() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.registry.robots["robot-01"].inject(estop=True)
        body = c.post(
            "/api/v1/tasks",
            headers=h,
            json={"robot_id": "robot-01", "point_id": "P9"},
        ).json()
        assert body["state"] == "Failed"
        assert body["error"]["code"] == "DEVICE_ESTOP"


def test_link_down_reconnect_then_fail() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.registry.robots["robot-01"].inject(link_down=True)
        body = c.post(
            "/api/v1/tasks",
            headers=h,
            json={"robot_id": "robot-01", "point_id": "P9"},
        ).json()
        assert body["state"] == "Failed"
        assert body["error"]["code"] == "DEVICE_OFFLINE"
        assert body["reconnects"] >= 1


def test_disconnect_reconnects_and_succeeds() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.registry.robots["robot-01"].disconnect()
        body = c.post(
            "/api/v1/tasks",
            headers=h,
            json={"robot_id": "robot-01", "point_id": "P3"},
        ).json()
        assert body["state"] == "Succeeded"
        assert body["reconnects"] >= 1


def test_exceed_alarm_ack_and_report() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.registry.instruments["pc-01"].inject(exceed=True)
        task = c.post(
            "/api/v1/tasks",
            headers=h,
            json={"robot_id": "robot-01", "point_id": "P4"},
        ).json()
        assert task["state"] == "Succeeded"
        assert task["alarms"]
        alarms = c.get("/api/v1/alarms", headers=h).json()
        assert any(a["state"] == "active" for a in alarms)
        aid = task["alarms"][0]
        ack = c.post(f"/api/v1/alarms/{aid}/ack", headers=h)
        assert ack.status_code == 200
        assert ack.json()["state"] == "acked"
        rpt = c.post("/api/v1/reports", headers=h, json={"task_id": task["id"]})
        assert rpt.status_code == 200, rpt.text
        fid = rpt.json()["id"]
        html = c.get(f"/api/v1/reports/{fid}/file", headers=h)
        assert html.status_code == 200
        assert task["id"] in html.text
        channels = next(s for s in task["samples"] if s["instrument_id"] == "pc-01")["readings"]
        assert [r["channel"] for r in channels] == ["0.1um", "0.5um", "1.0um", "5.0um"]


def test_geojson_import() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        doc = {
            "type": "FeatureCollection",
            "name": "lab",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": "P1", "name": "更衣室", "floor": 1},
                    "geometry": {"type": "Point", "coordinates": [1.2, 3.4]},
                }
            ],
        }
        imported = c.post("/api/v1/maps/import", headers=h, json=doc)
        assert imported.status_code == 200, imported.text
        assert imported.json()["points"][0]["name"] == "更衣室"
        listed = c.get("/api/v1/maps", headers=h).json()
        assert listed[0]["format"] == "geojson"


def test_process_lost_on_restart() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.store.save_task(
            {
                "id": "deadbeef0001",
                "state": "Running",
                "robot_id": "robot-01",
                "point_id": "P1",
                "skills": [],
                "elevator_id": None,
                "elevator_floor": None,
                "samples": [],
                "elevator_trace": [],
                "alarms": [],
                "reconnects": 0,
                "error": None,
                "queue_reason": None,
            }
        )
    with TestClient(app) as c:
        h = _auth(c)
        body = c.get("/api/v1/tasks/deadbeef0001", headers=h).json()
        assert body["state"] == "Failed"
        assert body["error"]["code"] == "PROCESS_LOST"


def test_stop_queued_task() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.mutex.acquire("elevator", "elev-01", holder="blocker", on_conflict="fail")
        queued = c.post(
            "/api/v1/tasks",
            headers=h,
            json={
                "robot_id": "robot-01",
                "point_id": "P1",
                "elevator_id": "elev-01",
                "elevator_floor": 2,
            },
        ).json()
        assert queued["state"] == "Queued"
        stopped = c.post(f"/api/v1/tasks/{queued['id']}/stop", headers=h)
        assert stopped.json()["state"] == "Cancelled"
        state.mutex.release("elevator", "elev-01", holder="blocker")


def test_fail_policy_marks_task_failed() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.features.on_conflict = "fail"
        state.mutex.acquire("point", "P1", holder="blocker", on_conflict="fail")
        try:
            body = c.post(
                "/api/v1/tasks",
                headers=h,
                json={"robot_id": "robot-01", "point_id": "P1"},
            ).json()
            assert body["state"] == "Failed"
            assert body["error"]["code"] == "CONFLICT_MUTEX"
        finally:
            state.features.on_conflict = "queue"
            state.mutex.release("point", "P1", holder="blocker")


def test_queue_wait_timeout() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        state.mutex.acquire("point", "P8", holder="blocker", on_conflict="fail")
        queued = c.post(
            "/api/v1/tasks",
            headers=h,
            json={"robot_id": "robot-01", "point_id": "P8"},
        ).json()
        assert queued["state"] == "Queued"
        queued["queued_at"] = 1.0
        state.store.save_task(queued)
        done = c.post(f"/api/v1/tasks/{queued['id']}/start", headers=h).json()
        assert done["state"] == "Failed"
        assert "超时" in done["error"]["message"]
        state.mutex.release("point", "P8", holder="blocker")


def test_zone_then_point_lock_order() -> None:
    with TestClient(app) as c:
        h = _auth(c)
        body = c.post(
            "/api/v1/tasks",
            headers=h,
            json={"robot_id": "robot-01", "zone_id": "z1", "point_id": "P7"},
        ).json()
        assert body["state"] == "Succeeded"
