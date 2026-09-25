from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import require
from app.core.security import Principal, parse_token
from app.main_state import features, get_secret

router = APIRouter(tags=["data"])


@router.get("/api/v1/points")
def list_points(_user: Annotated[Principal, Depends(require("settings.point.read"))]) -> list[dict[str, Any]]:
    return [{"id": "P1", "map_id": "map-01", "name": "更衣室", "pose": {"x": 1.0, "y": 2.0}}]


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
    return {"e_sign": features.e_sign, "limits": []}


@router.get("/api/v1/settings/features")
def get_features(_user: Annotated[Principal, Depends(require("settings.limit.read"))]) -> dict[str, Any]:
    return features.model_dump()


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


@router.websocket("/api/v1/ws")
async def ws_gateway(websocket: WebSocket, token: str | None = None) -> None:
    """实时通道占位：鉴权后可订阅 pose/task/alarm/measurement。"""
    await websocket.accept()
    raw = token or websocket.query_params.get("token")
    if not raw:
        await websocket.send_json({"code": "AUTH_REQUIRED", "message": "ws 需要 token"})
        await websocket.close(code=4401)
        return
    try:
        parse_token(raw, get_secret())
    except Exception as exc:  # noqa: BLE001
        await websocket.send_json({"code": "AUTH_REQUIRED", "message": str(exc)})
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
