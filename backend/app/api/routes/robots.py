from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.api.deps import require
from app.core.errors import DomainError
from app.core.security import Principal
from app.domain.models import Pose
from app.main_state import get_registry

router = APIRouter(prefix="/api/v1/robots", tags=["data"])


@router.get("")
def list_robots(_user: Annotated[Principal, Depends(require("data.robot.read"))]) -> list[dict[str, Any]]:
    reg = get_registry()
    out = []
    for rid, amr in reg.robots.items():
        st = amr.get_status()
        out.append({"id": rid, "status": asdict(st), "health": amr.health()})
    return out


@router.post("/{robot_id}/navigate")
def navigate(
    robot_id: str,
    body: dict[str, Any],
    _user: Annotated[Principal, Depends(require("operations.task.write"))],
) -> dict[str, Any]:
    amr = get_registry().robots.get(robot_id)
    if not amr:
        raise DomainError("NOT_FOUND", f"机器人 {robot_id} 不存在")
    pose = Pose(
        x=float(body.get("x", 0)),
        y=float(body.get("y", 0)),
        theta=float(body.get("theta", 0)),
        map_id=body.get("map_id"),
    )
    handle = amr.navigate_to(pose)
    return asdict(handle)
