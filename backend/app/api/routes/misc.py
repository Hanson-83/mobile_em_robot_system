from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

import app.main_state as state
from app.api.deps import require
from app.core.errors import DomainError
from app.core.security import Principal, parse_token
from app.main_state import get_secret

router = APIRouter(tags=["data"])


@router.get("/api/v1/points")
def list_points(_user: Annotated[Principal, Depends(require("settings.point.read"))]) -> list[dict[str, Any]]:
    return [{"id": "P1", "map_id": "map-01", "name": "更衣室", "pose": {"x": 1.0, "y": 2.0}}]


@router.post("/api/v1/points", tags=["settings"])
def create_point(
    body: dict[str, Any],
    _user: Annotated[Principal, Depends(require("settings.point.write"))],
) -> dict[str, Any]:
    return {"id": body.get("id", "P-new"), "note": "M1 placeholder"}


@router.patch("/api/v1/points/{point_id}", tags=["settings"])
def patch_point(
    point_id: str,
    _user: Annotated[Principal, Depends(require("settings.point.write"))],
) -> dict[str, str]:
    return {"id": point_id, "note": "M1 placeholder"}


@router.delete("/api/v1/points/{point_id}", tags=["settings"])
def delete_point(
    point_id: str,
    _user: Annotated[Principal, Depends(require("settings.point.write"))],
) -> dict[str, str]:
    return {"id": point_id, "deleted": "true"}


@router.get("/api/v1/measurements")
def list_measurements(_user: Annotated[Principal, Depends(require("data.measurement.read"))]) -> list[dict[str, Any]]:
    return []


@router.get("/api/v1/alarms")
def list_alarms(_user: Annotated[Principal, Depends(require("data.alarm.read"))]) -> list[dict[str, Any]]:
    return []


@router.get("/api/v1/maps")
def list_maps(_user: Annotated[Principal, Depends(require("data.map.read"))]) -> list[dict[str, Any]]:
    return [{"id": "map-01", "name": "占位地图（等待用户 AMR 地图格式）", "source": "placeholder"}]


@router.get("/api/v1/settings/limits")
def get_limits(_user: Annotated[Principal, Depends(require("settings.limit.read"))]) -> dict[str, Any]:
    return {"e_sign": state.features.e_sign, "limits": []}


@router.patch("/api/v1/settings/limits", tags=["settings"])
def patch_limits(_user: Annotated[Principal, Depends(require("settings.limit.write"))]) -> dict[str, Any]:
    if state.features.e_sign:
        raise DomainError("APPROVAL_REQUIRED", "签名开启时限值变更须经批准流")
    return {"updated": True, "note": "M1 placeholder"}


@router.get("/api/v1/settings/features")
def get_features(_user: Annotated[Principal, Depends(require("settings.limit.read"))]) -> dict[str, Any]:
    return state.features.model_dump()


@router.post("/api/v1/alarms/{alarm_id}/ack", tags=["operations"])
def ack_alarm(
    alarm_id: str,
    _user: Annotated[Principal, Depends(require("operations.alarm.ack"))],
) -> dict[str, str]:
    return {"id": alarm_id, "state": "acked", "note": "M1 placeholder"}


@router.post("/api/v1/alarms/{alarm_id}/close", tags=["operations"])
def close_alarm(
    alarm_id: str,
    _user: Annotated[Principal, Depends(require("operations.alarm.close"))],
) -> dict[str, str]:
    return {"id": alarm_id, "state": "closed", "note": "M1 placeholder"}


@router.get("/api/v1/alarms/export")
def export_alarms(_user: Annotated[Principal, Depends(require("data.alarm.export"))]) -> dict[str, str]:
    return {"format": "csv", "note": "M1 placeholder"}


@router.get("/api/v1/reports")
def list_reports(_user: Annotated[Principal, Depends(require("data.report.read"))]) -> list[dict[str, str]]:
    return []


@router.post("/api/v1/reports")
def create_report(_user: Annotated[Principal, Depends(require("data.report.write"))]) -> dict[str, str]:
    return {"id": "rpt-placeholder", "format": "html", "note": "M2/M3"}


@router.get("/api/v1/approvals", tags=["operations"])
def list_approvals(_user: Annotated[Principal, Depends(require("operations.approval.read"))]) -> list[dict[str, str]]:
    return []


@router.post("/api/v1/approvals", tags=["operations"])
def create_approval(_user: Annotated[Principal, Depends(require("operations.approval.write"))]) -> dict[str, str]:
    return {"id": "apr-placeholder", "state": "Draft", "note": "e_sign 关闭时主路径不创建"}


@router.get("/api/v1/users", tags=["settings"])
def list_users(_user: Annotated[Principal, Depends(require("settings.user.read"))]) -> list[dict[str, str]]:
    return [{"username": "admin", "roles": "admin"}]


@router.post("/api/v1/users", tags=["settings"])
def create_user(_user: Annotated[Principal, Depends(require("settings.user.write"))]) -> dict[str, str]:
    return {"id": "user-placeholder", "note": "M3"}


@router.websocket("/api/v1/ws")
async def ws_gateway(websocket: WebSocket, token: str | None = None) -> None:
    """实时通道占位：鉴权后可订阅 pose/task/alarm/measurement。"""
    await websocket.accept()
    raw = token or websocket.query_params.get("token")
    if not raw:
        await websocket.send_json(
            {"code": "AUTH_REQUIRED", "message": "ws 需要 token", "retryable": False}
        )
        await websocket.close(code=4401)
        return
    try:
        parse_token(raw, get_secret())
    except DomainError as exc:
        await websocket.send_json(exc.to_body())
        await websocket.close(code=4401)
        return
    await websocket.send_json({"type": "hello", "topics": ["pose", "task", "alarm", "measurement"]})
    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        return
