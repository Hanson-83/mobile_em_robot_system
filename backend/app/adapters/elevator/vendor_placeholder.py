"""真实电梯适配器占位。待用户提供楼控/电梯 API 后实现。"""

from __future__ import annotations

from typing import Any

from app.domain.dto import CommandHandle, ElevatorStatus


class ElevatorVendorX:
    def __init__(self, elevator_id: str, **_: Any) -> None:
        self.elevator_id = elevator_id
        raise NotImplementedError("ElevatorVendorX 等待用户提供电梯/楼控 API 文档")

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def health(self) -> dict[str, Any]:
        return {}

    async def get_status(self) -> ElevatorStatus:
        raise NotImplementedError

    async def call_elevator(self, floor: int, options: dict[str, Any] | None = None) -> CommandHandle:
        raise NotImplementedError

    async def enter_elevator(self, options: dict[str, Any] | None = None) -> CommandHandle:
        raise NotImplementedError

    async def exit_elevator(self, options: dict[str, Any] | None = None) -> CommandHandle:
        raise NotImplementedError
