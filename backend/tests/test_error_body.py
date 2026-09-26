from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_validation_and_404_use_domain_error_body() -> None:
    with TestClient(app) as c:
        r = c.post("/api/v1/auth/login", json={"username": "only"})
        assert r.status_code == 422
        body = r.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert body["retryable"] is False
        assert "message" in body
        nf = c.get("/api/v1/no-such-route")
        assert nf.status_code == 404
        assert nf.json()["code"] == "NOT_FOUND"
        assert nf.json()["retryable"] is False


def test_ws_snapshot_follows_hello() -> None:
    with TestClient(app) as c:
        tok = c.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"}).json()[
            "access_token"
        ]
        with c.websocket_connect(f"/api/v1/ws?token={tok}") as ws:
            assert ws.receive_json()["type"] == "hello"
            snap = ws.receive_json()
            assert snap["type"] == "snapshot"
            assert "alarms" in snap
            assert "robots" in snap


def test_ws_auth_error_has_retryable() -> None:
    with TestClient(app) as c:
        with c.websocket_connect("/api/v1/ws") as ws:
            msg = ws.receive_json()
            assert msg["code"] == "AUTH_REQUIRED"
            assert msg["retryable"] is False
