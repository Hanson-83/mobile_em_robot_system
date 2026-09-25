"""Gateway 最小资源表落地（DS §4.2）。未完成领域逻辑以内存/占位返回。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.api.deps import get_principal
from app.core.config import FeaturesFile
from app.core.errors import approval_required
from app.core.security import Principal, issue_token, parse_token
from app.domain.dto import MeasurementIn, Point, TaskCreate

ops = APIRouter(prefix="/api/v1", tags=["operations"])
data = APIRouter(prefix="/api/v1", tags=["data"])
settings_api = APIRouter(prefix="/api/v1", tags=["settings"])


class LoginBody(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class LimitsPatch(BaseModel):
    limits: dict[str, float]


@ops.post("/auth/login")
def login(body: LoginBody, request: Request) -> TokenOut:
    user = request.app.state.users.authenticate(body.username, body.password)
    features: FeaturesFile = request.app.state.features
    token = issue_token(
        request.app.state.settings.jwt_secret,
        user.username,
        user.role,
        features.security.session_ttl_min,
    )
    return TokenOut(access_token=token, role=user.role)


@ops.get("/tasks")
def list_tasks(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("operations.task.read")
    return [t.model_dump(mode="json") for t in request.app.state.stores.tasks.values()]


@ops.post("/tasks", status_code=201)
def create_task(
    body: TaskCreate,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("operations.task.write")
    return request.app.state.stores.create_task(body).model_dump(mode="json")


@ops.post("/tasks/{task_id}/cancel")
def cancel_task(
    task_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("operations.task.write")
    return request.app.state.stores.cancel_task(task_id).model_dump(mode="json")


@ops.post("/alarms/{alarm_id}/ack")
def ack_alarm(
    alarm_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("operations.alarm.ack")
    return request.app.state.stores.ack_alarm(alarm_id, principal.sub).model_dump(mode="json")


@ops.post("/alarms/{alarm_id}/close")
def close_alarm(
    alarm_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("operations.alarm.close")
    return request.app.state.stores.close_alarm(alarm_id, principal.sub).model_dump(mode="json")


@ops.get("/approvals")
def list_approvals(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("operations.approval.read")
    return [a.model_dump(mode="json") for a in request.app.state.stores.approvals.values()]


@ops.post("/approvals")
def create_approval(
    body: dict[str, Any],
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("operations.approval.write")
    req = request.app.state.stores.create_approval(
        str(body.get("object_ref", "")),
        str(body.get("action", "")),
        body.get("payload") or {},
    )
    return req.model_dump(mode="json")


@ops.post("/approvals/{approval_id}/approve")
def approve(
    approval_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("operations.approval.write")
    return request.app.state.stores.decide_approval(approval_id, True).model_dump(mode="json")


@data.get("/measurements")
def list_measurements(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("data.measurement.read")
    return [m.model_dump(mode="json") for m in request.app.state.stores.measurements.values()]


@data.post("/measurements")
def ingest_measurement(
    body: MeasurementIn,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("data.measurement.read")
    item = request.app.state.stores.upsert_measurement(body)
    out = item.model_dump(mode="json")
    if item.replay:
        out["code"] = "IDEMPOTENCY_REPLAY"
    return out


@data.get("/alarms")
def list_alarms(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("data.alarm.read")
    return [a.model_dump(mode="json") for a in request.app.state.stores.alarms.values()]


@data.get("/alarms/export")
def export_alarms(request: Request, principal: Principal = Depends(get_principal)) -> dict:
    principal.require("data.alarm.export")
    rows = request.app.state.stores.alarms.values()
    csv_text = "id,severity,state,message,ts\n" + "\n".join(
        f"{a.id},{a.severity},{a.state.value},{a.message},{a.ts.isoformat()}" for a in rows
    )
    return {"format": "csv", "content": csv_text}


@data.get("/reports")
def list_reports(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("data.report.read")
    return [r.model_dump(mode="json") for r in request.app.state.stores.reports.values()]


@data.post("/reports")
def create_report(
    body: dict[str, Any],
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("data.report.write")
    return request.app.state.stores.add_report(str(body.get("task_ref", "unknown"))).model_dump(
        mode="json"
    )


@data.get("/robots")
async def list_robots(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("data.robot.read")
    out = []
    for adapter in request.app.state.registry.robots.values():
        status = await adapter.get_status()
        out.append(status.model_dump(mode="json"))
    return out


@data.get("/maps")
def list_maps(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("data.map.read")
    return request.app.state.stores.maps


@settings_api.get("/points")
def list_points(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("settings.point.read")
    return [p.model_dump(mode="json") for p in request.app.state.stores.points.values()]


@settings_api.post("/points", status_code=201)
def create_point(
    body: Point,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("settings.point.write")
    return request.app.state.stores.create_point(body).model_dump(mode="json")


@settings_api.get("/settings/limits")
def get_limits(request: Request, principal: Principal = Depends(get_principal)) -> dict:
    principal.require("settings.limit.read")
    return {"limits": request.app.state.stores.limits}


@settings_api.patch("/settings/limits")
def patch_limits(
    body: LimitsPatch,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    principal.require("settings.limit.write")
    features: FeaturesFile = request.app.state.features
    if features.e_sign:
        req = request.app.state.stores.create_approval(
            "settings.limits", "patch_limits", body.limits
        )
        raise approval_required(f"需批准: {req.id}")
    request.app.state.stores.limits.update(body.limits)
    return {"limits": request.app.state.stores.limits}


@settings_api.get("/users")
def list_users(request: Request, principal: Principal = Depends(get_principal)) -> list[dict]:
    principal.require("settings.user.read")
    return request.app.state.users.list_public()


@settings_api.get("/settings/features")
def get_features(request: Request, principal: Principal = Depends(get_principal)) -> dict:
    principal.require("settings.feature.read")
    return request.app.state.features.model_dump()


@ops.websocket("/ws")
async def ws_channel(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    """MVP 锁定 WebSocket。M1 仅握手 + 订阅确认。"""
    app = websocket.app
    if not token:
        await websocket.close(code=4401)
        return
    try:
        parse_token(app.state.settings.jwt_secret, token)
    except Exception:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    await websocket.send_json(
        {"type": "subscribed", "topics": ["pose", "task", "alarm", "measurement"]}
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
