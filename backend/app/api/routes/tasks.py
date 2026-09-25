from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import require
from app.core.errors import DomainError
from app.core.security import Principal
from app.main_state import get_registry, mutex

router = APIRouter(prefix="/api/v1/tasks", tags=["operations"])

_TASKS: dict[str, dict[str, Any]] = {}


class TaskCreate(BaseModel):
    robot_id: str
    point_id: str | None = None
    skills: list[str] = ["navigate", "sample"]
    elevator_id: str | None = None
    elevator_floor: int | None = None


@router.get("")
def list_tasks(_user: Annotated[Principal, Depends(require("operations.task.read"))]) -> list[dict[str, Any]]:
    return list(_TASKS.values())


@router.post("")
def create_task(
    body: TaskCreate,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    """M1 冒烟：同步跑 Fake 技能链（导航+可选电梯+采样）。完整状态机属 M2。"""
    tid = uuid4().hex[:12]
    reg = get_registry()
    amr = reg.robots.get(body.robot_id)
    if not amr:
        raise DomainError("NOT_FOUND", f"机器人 {body.robot_id} 不存在")

    if body.point_id:
        mutex.acquire("point", body.point_id, holder=tid, on_conflict="fail")

    samples: list[dict[str, Any]] = []
    elevator_trace: list[str] = []
    try:
        amr.navigate_to(body.point_id or "P0")
        if body.elevator_id:
            elv = reg.elevators.get(body.elevator_id)
            if not elv:
                raise DomainError("NOT_FOUND", f"电梯 {body.elevator_id} 不存在")
            mutex.acquire("elevator", body.elevator_id, holder=tid, on_conflict="fail")
            try:
                floor = body.elevator_floor if body.elevator_floor is not None else 2
                elevator_trace.append(elv.call_elevator(floor).status)
                elevator_trace.append(elv.enter_elevator().status)
                elevator_trace.append(elv.exit_elevator().status)
            finally:
                mutex.release("elevator", body.elevator_id, holder=tid)
        for iid, inst in reg.instruments.items():
            if hasattr(inst, "start_sample"):
                inst.start_sample()
                readings = inst.read_channels()
                samples.append({"instrument_id": iid, "readings": [asdict(r) for r in readings]})
                inst.stop_sample()
            elif hasattr(inst, "read_temp_humidity"):
                samples.append({"instrument_id": iid, "readings": asdict(inst.read_temp_humidity())})
            elif hasattr(inst, "read_air_speed"):
                samples.append({"instrument_id": iid, "readings": asdict(inst.read_air_speed())})
        rec = {
            "id": tid,
            "state": "Succeeded",
            "robot_id": body.robot_id,
            "point_id": body.point_id,
            "skills": body.skills,
            "samples": samples,
            "elevator_trace": elevator_trace,
        }
    except Exception:
        rec = {
            "id": tid,
            "state": "Failed",
            "robot_id": body.robot_id,
            "point_id": body.point_id,
            "skills": body.skills,
        }
        _TASKS[tid] = rec
        raise
    finally:
        if body.point_id:
            mutex.release("point", body.point_id, holder=tid)
    _TASKS[tid] = rec
    return rec


@router.post("/{id}/cancel")
def cancel_task(
    id: str,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    rec = _TASKS.get(id)
    if not rec:
        raise DomainError("NOT_FOUND", f"任务 {id} 不存在")
    rec["state"] = "Cancelled"
    return rec
