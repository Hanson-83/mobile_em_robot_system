"""真实 AMR 适配器占位。待用户提供厂商 HTTP API 文档后实现。"""

from __future__ import annotations

from typing import Any

from app.domain.dto import CommandHandle, Pose, RobotStatus


class AmrVendorX:
    """占位实现：不可用于运行；Factory 在装配时即拒绝。"""

    robot_id: str

    def __init__(self, robot_id: str, **_: Any) -> None:
        self.robot_id = robot_id
        raise NotImplementedError(
            "AmrVendorX 等待用户提供 AMR API 文档（导航/状态/充电/地图同步，不含电梯）"
        )

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def health(self) -> dict[str, Any]:
        return {}

    async def get_status(self) -> RobotStatus:
        raise NotImplementedError

    async def navigate_to(
        self, target: Pose | str, options: dict[str, Any] | None = None
    ) -> CommandHandle:
        raise NotImplementedError

    async def cancel(self, command_id: str | None = None) -> None:
        raise NotImplementedError

    async def dock_charge(self) -> CommandHandle:
        raise NotImplementedError

    def subscribe_telemetry(self, callback: Any) -> None:
        raise NotImplementedError

    def unsubscribe(self) -> None:
        raise NotImplementedError
