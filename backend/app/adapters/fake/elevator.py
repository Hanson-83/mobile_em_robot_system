from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.errors import DomainError
from app.domain.models import CommandHandle, ElevatorStatus


class ElevatorFake:
    """Call/Enter/Exit 可演；可注入失败。"""

    def __init__(self, device_id: str, floors: list[int] | None = None, *, delay_s: float = 0.02, **_k: Any) -> None:
        self.device_id = device_id
        self.floors = floors or [1, 2, 3]
        self.delay_s = delay_s
        self._connected = False
        self._status = ElevatorStatus(floor=self.floors[0], door="closed", online=False)
        self._fail_next: str | None = None

    def connect(self) -> None:
        self._connected = True
        self._status.online = True

    def disconnect(self) -> None:
        self._connected = False
        self._status.online = False

    def health(self) -> dict[str, Any]:
        return {"id": self.device_id, "type": "elevator_fake", "online": self._connected}

    def get_status(self) -> ElevatorStatus:
        self._ensure()
        return self._status

    def call_elevator(self, floor: int, options: dict[str, Any] | None = None) -> CommandHandle:
        self._ensure()
        self._maybe_fail("call")
        if floor not in self.floors:
            raise DomainError("VALIDATION_ERROR", f"楼层 {floor} 不在 {self.floors}")
        time.sleep(float((options or {}).get("delay_s", self.delay_s)))
        self._status.floor = floor
        self._status.door = "open"
        self._status.moving = False
        return CommandHandle(command_id=uuid.uuid4().hex[:12], status="succeeded")

    def enter_elevator(self, options: dict[str, Any] | None = None) -> CommandHandle:
        self._ensure()
        self._maybe_fail("enter")
        time.sleep(float((options or {}).get("delay_s", self.delay_s)))
        self._status.door = "closed"
        return CommandHandle(command_id=uuid.uuid4().hex[:12], status="succeeded")

    def exit_elevator(self, options: dict[str, Any] | None = None) -> CommandHandle:
        self._ensure()
        self._maybe_fail("exit")
        time.sleep(float((options or {}).get("delay_s", self.delay_s)))
        self._status.door = "open"
        return CommandHandle(command_id=uuid.uuid4().hex[:12], status="succeeded")

    def inject(self, **kwargs: Any) -> None:
        if "fail_next" in kwargs:
            self._fail_next = kwargs["fail_next"]
        if kwargs.get("offline"):
            self._connected = False
            self._status.online = False

    def _maybe_fail(self, op: str) -> None:
        if self._fail_next in (op, "any"):
            self._fail_next = None
            raise DomainError("DEVICE_OFFLINE", f"ElevatorFake 注入失败: {op}", retryable=True)

    def _ensure(self) -> None:
        if not self._connected or not self._status.online:
            raise DomainError("DEVICE_OFFLINE", f"电梯 {self.device_id} 离线")
