from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

import app.main_state as state
from app.api.deps import require
from app.core.errors import DomainError
from app.core.security import Principal, parse_token
from app.main_state import get_secret

router = APIRouter(tags=["data"])


@router.get("/api/v1/measurements")
def list_measurements(_user: Annotated[Principal, Depends(require("data.measurement.read"))]) -> list[dict[str, Any]]:
    assert state.store is not None
    return state.store.list_measurements()


@router.get("/api/v1/alarms")
def list_alarms(_user: Annotated[Principal, Depends(require("data.alarm.read"))]) -> list[dict[str, Any]]:
    assert state.store is not None
    return state.store.list_alarms()


@router.get("/api/v1/realtime")
def realtime(_user: Annotated[Principal, Depends(require("data.measurement.read"))]) -> dict[str, Any]:
    assert state.store is not None
    alarms = [a for a in state.store.list_alarms() if a.get("state") == "active"]
    robots = []
    if state.registry:
        from dataclasses import asdict

        for rid, amr in state.registry.robots.items():
            robots.append({"id": rid, "status": asdict(amr.get_status())})
    return {"robots": robots, "alarms": alarms, "measurements": state.store.list_measurements()}


@router.get("/api/v1/maps")
def list_maps(_user: Annotated[Principal, Depends(require("data.map.read"))]) -> list[dict[str, Any]]:
    if state.maps:
        return state.maps
    return [
        {
            "id": "map-01",
            "name": "占位地图",
            "format": "geojson",
            "source": "placeholder",
            "note": "导入 POST /api/v1/maps/import ，常见 GeoJSON Point 点位",
        }
    ]


@router.post("/api/v1/maps/import", tags=["settings"])
def import_map(
    body: dict[str, Any],
    _user: Annotated[Principal, Depends(require("settings.point.write"))],
) -> dict[str, Any]:
    if body.get("type") != "FeatureCollection":
        raise DomainError("VALIDATION_ERROR", "仅接受 GeoJSON FeatureCollection")
    points = []
    for feat in body.get("features") or []:
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates") or [0, 0]
        props = feat.get("properties") or {}
        points.append(
            {
                "id": props.get("id") or props.get("name"),
                "name": props.get("name"),
                "x": coords[0],
                "y": coords[1] if len(coords) > 1 else 0,
                "floor": props.get("floor"),
            }
        )
    rec = {
        "id": body.get("id") or "map-import",
        "name": body.get("name") or "imported",
        "format": "geojson",
        "source": "import",
        "points": points,
        "note": "市面常见 GeoJSON 点位；ROS map yaml+pgm 仍为占位未解析",
    }
    state.maps = [rec]
    return rec


@router.get("/api/v1/settings/features")
def get_features(_user: Annotated[Principal, Depends(require("settings.limit.read"))]) -> dict[str, Any]:
    return state.features.model_dump()


@router.post("/api/v1/alarms/{alarm_id}/ack", tags=["operations"])
def ack_alarm(
    alarm_id: str,
    user: Annotated[Principal, Depends(require("operations.alarm.ack"))],
) -> dict[str, Any]:
    assert state.store is not None
    alarm = state.store.update_alarm(alarm_id, state="acked", ack_by=user.username)
    if not alarm:
        raise DomainError("NOT_FOUND", f"报警 {alarm_id} 不存在")
    return alarm


@router.post("/api/v1/alarms/{alarm_id}/close", tags=["operations"])
def close_alarm(
    alarm_id: str,
    user: Annotated[Principal, Depends(require("operations.alarm.close"))],
) -> dict[str, Any]:
    assert state.store is not None
    alarm = state.store.update_alarm(alarm_id, state="closed", closed_by=user.username)
    if not alarm:
        raise DomainError("NOT_FOUND", f"报警 {alarm_id} 不存在")
    return alarm


@router.get("/api/v1/alarms/export")
def export_alarms(_user: Annotated[Principal, Depends(require("data.alarm.export"))]) -> dict[str, str]:
    assert state.store is not None
    lines = ["id,state,severity,message"]
    for a in state.store.list_alarms():
        msg = str(a.get("message", "")).replace(",", " ")
        lines.append(f"{a.get('id')},{a.get('state')},{a.get('severity')},{msg}")
    return {"format": "csv", "content": "\n".join(lines)}


@router.get("/api/v1/reports")
def list_reports(_user: Annotated[Principal, Depends(require("data.report.read"))]) -> list[dict[str, Any]]:
    assert state.store is not None
    return [
        {k: r[k] for k in ("id", "task_id", "format") if k in r} for r in state.store.list_reports()
    ]


@router.post("/api/v1/reports")
def create_report(
    body: dict[str, Any],
    _user: Annotated[Principal, Depends(require("data.report.write"))],
) -> dict[str, str]:
    from app.services.report import write_report

    assert state.store is not None
    task_id = body.get("task_id")
    if not task_id:
        raise DomainError("VALIDATION_ERROR", "缺少 task_id")
    task = state.store.get_task(str(task_id))
    if not task:
        raise DomainError("NOT_FOUND", f"任务 {task_id} 不存在")
    rec = write_report(task, state.report_dir)
    state.store.save_report(rec)
    return {"id": rec["id"], "task_id": rec["task_id"], "format": rec["format"]}


@router.get("/api/v1/reports/{report_id}/file")
def report_file(
    report_id: str,
    _user: Annotated[Principal, Depends(require("data.report.read"))],
):
    from fastapi.responses import FileResponse

    assert state.store is not None
    rec = state.store.get_report(report_id)
    if not rec:
        raise DomainError("NOT_FOUND", f"报告 {report_id} 不存在")
    return FileResponse(rec["path"], media_type="text/html")


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
