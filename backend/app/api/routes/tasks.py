from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

import app.main_state as state
from app.api.deps import require
from app.core.security import Principal

router = APIRouter(prefix="/api/v1/tasks", tags=["operations"])


class TaskCreate(BaseModel):
    robot_id: str
    point_id: str | None = None
    skills: list[str] = Field(default_factory=lambda: ["navigate", "sample"])
    elevator_id: str | None = None
    elevator_floor: int | None = None
    auto_start: bool = True


def _sched():
    assert state.scheduler is not None
    return state.scheduler


@router.get("")
def list_tasks(_user: Annotated[Principal, Depends(require("operations.task.read"))]) -> list[dict[str, Any]]:
    assert state.store is not None
    return state.store.list_tasks()


@router.post("")
def create_task(
    body: TaskCreate,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    return _sched().submit(body.model_dump(), auto_start=body.auto_start)


@router.get("/{id}")
def get_task(
    id: str,
    _user: Annotated[Principal, Depends(require("operations.task.read"))],
) -> dict[str, Any]:
    from app.core.errors import DomainError

    assert state.store is not None
    task = state.store.get_task(id)
    if not task:
        raise DomainError("NOT_FOUND", f"任务 {id} 不存在")
    return task


@router.post("/{id}/start")
def start_task(
    id: str,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    return _sched().start(id)


@router.post("/{id}/stop")
def stop_task(
    id: str,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    return _sched().stop(id)


@router.post("/{id}/cancel")
def cancel_task(
    id: str,
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    return _sched().stop(id)
