from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import app.main_state as state
from app.main import app


def _token(c: TestClient, user: str, password: str) -> dict[str, str]:
    tok = c.post("/api/v1/auth/login", json={"username": user, "password": password}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {tok}"}


def test_point_crud_and_operator_forbidden() -> None:
    with TestClient(app) as c:
        admin = _token(c, "admin", "admin")
        operator = _token(c, "operator", "operator")
        denied = c.patch(
            "/api/v1/settings/limits",
            headers=operator,
            json={"temperature_c": {"max": 1}},
        )
        assert denied.status_code == 403
        created = c.post(
            "/api/v1/points",
            headers=admin,
            json={"id": "P9", "name": "缓冲间", "map_id": "map-01", "pose": {"x": 1, "y": 2}},
        )
        assert created.status_code == 200, created.text
        assert c.get("/api/v1/points", headers=admin).json()[0]["id"] == "P9"
        patched = c.patch("/api/v1/points/P9", headers=admin, json={"name": "缓冲间-2"})
        assert patched.json()["name"] == "缓冲间-2"


def test_esign_off_applies_immediately() -> None:
    with TestClient(app) as c:
        admin = _token(c, "admin", "admin")
        res = c.patch(
            "/api/v1/settings/limits",
            headers=admin,
            json={"temperature_c": {"max": 28}},
        )
        assert res.status_code == 200, res.text
        assert res.json()["applied"] is True
        limits = c.get("/api/v1/settings/limits", headers=admin).json()["limits"]
        assert limits["temperature_c"]["max"] == 28


def test_esign_on_requires_other_approver() -> None:
    with TestClient(app) as c:
        admin = _token(c, "admin", "admin")
        approver = _token(c, "approver", "approver")
        c.patch("/api/v1/settings/features", headers=admin, json={"e_sign": True, "audit_trail": True})
        blocked = c.patch(
            "/api/v1/settings/limits",
            headers=admin,
            json={"temperature_c": {"max": 15}},
        )
        assert blocked.status_code == 409
        assert blocked.json()["code"] == "APPROVAL_REQUIRED"
        assert c.get("/api/v1/settings/limits", headers=admin).json()["limits"]["temperature_c"]["max"] != 15
        aid = blocked.json()["details"]["approval_id"]
        self_approve = c.post(
            f"/api/v1/approvals/{aid}/decide",
            headers=admin,
            json={"decision": "approved", "password": "admin", "meaning": "本人"},
        )
        assert self_approve.status_code == 403
        done = c.post(
            f"/api/v1/approvals/{aid}/decide",
            headers=approver,
            json={"decision": "approved", "password": "approver", "meaning": "确认限值"},
        )
        assert done.status_code == 200, done.text
        assert done.json()["state"] == "Approved"
        assert c.get("/api/v1/settings/limits", headers=admin).json()["limits"]["temperature_c"]["max"] == 15
        audits = c.get("/api/v1/audit", headers=admin).json()
        assert any(a["action"] == "approval.approve" for a in audits)
        removed = c.delete(f"/api/v1/audit/{audits[0]['id']}", headers=admin)
        assert removed.status_code == 403
        assert removed.json()["code"] == "FORBIDDEN"


def test_reject_and_expire_do_not_apply() -> None:
    with TestClient(app) as c:
        admin = _token(c, "admin", "admin")
        approver = _token(c, "approver", "approver")
        c.patch("/api/v1/settings/features", headers=admin, json={"e_sign": True})
        rejected = c.patch(
            "/api/v1/settings/limits",
            headers=admin,
            json={"humidity_pct": {"max": 10}},
        )
        aid = rejected.json()["details"]["approval_id"]
        no = c.post(
            f"/api/v1/approvals/{aid}/decide",
            headers=approver,
            json={"decision": "rejected", "password": "approver", "meaning": "驳回"},
        )
        assert no.json()["state"] == "Rejected"
        assert c.get("/api/v1/settings/limits", headers=admin).json()["limits"]["humidity_pct"]["max"] != 10
        expired = c.patch(
            "/api/v1/settings/limits",
            headers=admin,
            json={"humidity_pct": {"max": 12}},
        )
        eid = expired.json()["details"]["approval_id"]
        item = state.store.get_approval(eid)
        assert item is not None
        item["expires_at"] = 1
        state.store.save_approval(item)
        late = c.post(
            f"/api/v1/approvals/{eid}/decide",
            headers=approver,
            json={"decision": "approved", "password": "approver", "meaning": "过期"},
        )
        assert late.status_code == 409
        assert late.json()["code"] == "APPROVAL_REJECTED"
        assert c.get("/api/v1/settings/limits", headers=admin).json()["limits"]["humidity_pct"]["max"] != 12


def test_backup_restore_roundtrip(tmp_path: Path) -> None:
    with TestClient(app) as c:
        admin = _token(c, "admin", "admin")
        cfg = tmp_path / "cfg"
        cfg.mkdir()
        (cfg / "features.example.yaml").write_text("e_sign: false\n", encoding="utf-8")
        state.config_dir = cfg
        state.report_dir.mkdir(parents=True, exist_ok=True)
        (state.report_dir / "note.html").write_text("<p>keep</p>", encoding="utf-8")
        assert c.post(
            "/api/v1/points",
            headers=admin,
            json={"id": "PB", "name": "备份点"},
        ).status_code == 200
        assert c.patch(
            "/api/v1/settings/limits",
            headers=admin,
            json={"temperature_c": {"max": 21}},
        ).status_code == 200
        saved = c.post("/api/v1/admin/backup", headers=admin)
        assert saved.status_code == 200, saved.text
        bid = saved.json()["id"]
        assert "features.example.yaml" in saved.json()["manifest"]["config_files"]
        c.patch(
            "/api/v1/settings/limits",
            headers=admin,
            json={"temperature_c": {"max": 99}},
        )
        c.delete("/api/v1/points/PB", headers=admin)
        (state.report_dir / "note.html").unlink()
        restored = c.post("/api/v1/admin/restore", headers=admin, json={"id": bid})
        assert restored.status_code == 200, restored.text
        ids = [p["id"] for p in c.get("/api/v1/points", headers=admin).json()]
        assert "PB" in ids
        assert (state.report_dir / "note.html").read_text(encoding="utf-8") == "<p>keep</p>"
        assert c.get("/api/v1/settings/limits", headers=admin).json()["limits"]["temperature_c"]["max"] == 21
        db = Path(saved.json()["path"]) / "mer.sqlite"
        db.write_bytes(db.read_bytes() + b"x")
        bad = c.post("/api/v1/admin/restore", headers=admin, json={"id": bid})
        assert bad.status_code == 422
        assert bad.json()["code"] == "VALIDATION_ERROR"


def test_limits_survive_restart_and_point_cannot_bypass() -> None:
    with TestClient(app) as c:
        admin = _token(c, "admin", "admin")
        assert c.patch(
            "/api/v1/settings/limits",
            headers=admin,
            json={"temperature_c": {"max": 19}},
        ).status_code == 200
        c.patch("/api/v1/settings/features", headers=admin, json={"e_sign": True})
        blocked = c.patch(
            "/api/v1/points/nope",
            headers=admin,
            json={"limits": {"temperature_c": {"max": 1}}},
        )
        assert blocked.status_code == 422
    with TestClient(app) as c:
        admin = _token(c, "admin", "admin")
        assert c.get("/api/v1/settings/limits", headers=admin).json()["limits"]["temperature_c"]["max"] == 19
    with TestClient(app) as c:
        admin = _token(c, "admin", "admin")
        task = c.post(
            "/api/v1/tasks",
            headers=admin,
            json={"robot_id": "robot-01", "point_id": "P1"},
        )
        assert task.status_code == 200, task.text
        series = c.get("/api/v1/trends", headers=admin, params={"metric": "0.5um"})
        assert series.status_code == 200
        assert series.json()["series"]
        assert series.json()["series"][0]["unit"] == "count/cf"
