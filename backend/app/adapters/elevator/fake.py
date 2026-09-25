"""ElevatorFake：Call/Enter/Exit 可演；可注入失败。"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.core.errors import DomainError, device_offline
from app.domain.dto import CommandHandle, ElevatorStatus


class ElevatorFake:
    def __init__(
        self,
        elevator_id: str,
        *,
        floors: list[int] | None = None,
        delay_s: float = 0.01,
    ) -> None:
        self.elevator_id = elevator_id
        self.floors = floors or [1, 2, 3]
        self.delay_s = delay_s
        self._connected = False
        self._fail_next: str | None = None
        self._status = ElevatorStatus(
            elevator_id=elevator_id,
            floor=self.floors[0],
            door="closed",
            online=False,
        )

    def _guard(self) -> None:
        if not self._connected or not self._status.online:
            raise device_offline(f"电梯 {self.elevator_id} 离线")

    def _maybe_fail(self, action: str) -> None:
        if self._fail_next == action or self._fail_next == "*":
            self._fail_next = None
            raise DomainError(
                "DEVICE_OFFLINE",
                f"ElevatorFake 注入失败: {action}",
                retryable=True,
                status_code=503,
            )

    async def connect(self) -> None:
        self._connected = True
        self._status.online = True

    async def disconnect(self) -> None:
        self._connected = False
        self._status.online = False

    async def start(self) -> None:
        await self.connect()

    async def stop(self) -> None:
        await self.disconnect()

    async def health(self) -> dict[str, Any]:
        return {
            "ok": self._connected and self._status.online,
            "type": "elevator_fake",
            "id": self.elevator_id,
        }

    async def get_status(self) -> ElevatorStatus:
        return self._status.model_copy(deep=True)

    async def call_elevator(self, floor: int, options: dict[str, Any] | None = None) -> CommandHandle:
        self._guard()
        self._maybe_fail("call")
        if floor not in self.floors:
            raise DomainError("VALIDATION_ERROR", f"楼层 {floor} 不在 {self.floors}", status_code=422)
        self._status.busy = True
        await asyncio.sleep(self.delay_s)
        self._status.floor = floor
        self._status.door = "open"
        self._status.busy = False
        return CommandHandle(command_id=str(uuid.uuid4()), status="succeeded")

    async def enter_elevator(self, options: dict[str, Any] | None = None) -> CommandHandle:
        self._guard()
        self._maybe_fail("enter")
        await asyncio.sleep(self.delay_s)
        self._status.door = "closed"
        return CommandHandle(command_id=str(uuid.uuid4()), status="succeeded")

    async def exit_elevator(self, options: dict[str, Any] | None = None) -> CommandHandle:
        self._guard()
        self._maybe_fail("exit")
        await asyncio.sleep(self.delay_s)
        self._status.door = "open"
        return CommandHandle(command_id=str(uuid.uuid4()), status="succeeded")

    def inject(self, *, fail_next: str | None = None, offline: bool | None = None) -> None:
        if fail_next is not None:
            self._fail_next = fail_next
        if offline is True:
            self._status.online = False
        elif offline is False:
            self._status.online = True
