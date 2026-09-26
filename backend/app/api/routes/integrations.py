"""MES / SCADA / DCS 首批对接门面。只暴露已确认的任务与实时能力。"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

import app.main_state as state
from app.api.deps import require
from app.core.errors import DomainError
from app.core.integrations import describe_mes_catalog
from app.core.security import Principal

router = APIRouter(prefix="/api/v1/integrations/mes", tags=["integrations"])


class MesTaskCreate(BaseModel):
    robot_id: str
    point_id: str | None = None
    elevator_id: str | None = None
    elevator_floor: int | None = None
    auto_start: bool = True
    skills: list[str] = Field(default_factory=lambda: ["navigate", "sample"])
    client_request_id: str | None = None


def _sched():
    assert state.scheduler is not None
    return state.scheduler


@router.get("/catalog")
def mes_catalog(_user: Annotated[Principal, Depends(require("operations.task.read"))]) -> dict[str, Any]:
    return describe_mes_catalog()


@router.get("/tasks")
def list_tasks(_user: Annotated[Principal, Depends(require("operations.task.read"))]) -> list[dict[str, Any]]:
    assert state.store is not None
    return state.store.list_tasks()


@router.get("/tasks/{id}")
def get_task(
    id: str,
    _user: Annotated[Principal, Depends(require("operations.task.read"))],
) -> dict[str, Any]:
    assert state.store is not None
    task = state.store.get_task(id)
    if not task:
        raise DomainError("NOT_FOUND", f"任务 {id} 不存在")
    return task


@router.post("/tasks")
def create_task(
    body: MesTaskCreate,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    payload = body.model_dump()
    client_request_id = payload.pop("client_request_id", None)
    auto_start = bool(payload.pop("auto_start", True))
    task = _sched().submit(payload, auto_start=auto_start)
    if client_request_id:
        task["client_request_id"] = client_request_id
        assert state.store is not None
        state.store.save_task(task)
    return task


@router.post("/tasks/{id}/start")
def start_task(
    id: str,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    return _sched().start(id)


@router.post("/tasks/{id}/stop")
def stop_task(
    id: str,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    return _sched().stop(id)


@router.get("/realtime")
def realtime(_user: Annotated[Principal, Depends(require("data.measurement.read"))]) -> dict[str, Any]:
    assert state.store is not None
    from dataclasses import asdict

    alarms = [a for a in state.store.list_alarms() if a.get("state") == "active"]
    robots = []
    if state.registry:
        for rid, amr in state.registry.robots.items():
            robots.append({"id": rid, "status": asdict(amr.get_status())})
    return {
        "robots": robots,
        "alarms": alarms,
        "measurements": state.store.list_measurements(),
        "tasks": [
            {"id": t["id"], "state": t["state"], "robot_id": t.get("robot_id")}
            for t in state.store.list_tasks()
        ],
    }
