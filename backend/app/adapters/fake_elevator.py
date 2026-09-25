"""ElevatorFake：Call / Enter / Exit。独立于 AmrAdapter。"""

from __future__ import annotations

from app.adapters.support import AdapterMixin
from app.core.errors import AppError
from app.domain.dto import ElevatorStatus


class ElevatorFake(AdapterMixin):
    def __init__(self, device_id: str, floors: list[int] | None = None, adapter_type: str = "elevator_fake") -> None:
        super().__init__(device_id, adapter_type)
        self.floors = floors or [1, 2, 3]
        self.current_floor = self.floors[0]
        self.door = "closed"
        self.occupied = False
        self.fail_next: str | None = None
        self.history: list[str] = []

    def get_status(self) -> ElevatorStatus:
        return ElevatorStatus(
            online=self._connected,
            current_floor=self.current_floor,
            door=self.door,
            moving=False,
            fault_code="INJECTED" if self.fail_next else None,
        )

    def inject_failure(self, action: str = "call") -> None:
        self.fail_next = action

    def _guard(self, action: str):
        self._before_io()
        if self.fail_next in {action, "any"}:
            self.fail_next = None
            raise AppError("DEVICE_OFFLINE", f"电梯 {action} 失败（注入）", retryable=True, status_code=503)

    def call_elevator(self, floor: int, options: dict | None = None):
        self._guard("call")
        if floor not in self.floors:
            raise AppError("VALIDATION_ERROR", f"楼层 {floor} 不在配置中", status_code=422)
        self.current_floor = floor
        self.door = "open"
        self.history.append(f"call:{floor}")
        return self._handle("done", f"call:{floor}")

    def enter_elevator(self, options: dict | None = None):
        self._guard("enter")
        if self.door != "open":
            raise AppError("DEVICE_OFFLINE", "电梯门未开，无法进入", retryable=True, status_code=503)
        self.occupied = True
        self.door = "closed"
        self.history.append("enter")
        return self._handle("done", "enter")

    def exit_elevator(self, options: dict | None = None):
        self._guard("exit")
        floor = (options or {}).get("floor", self.current_floor)
        if floor not in self.floors:
            raise AppError("VALIDATION_ERROR", f"楼层 {floor} 不在配置中", status_code=422)
        self.current_floor = floor
        self.door = "open"
        self.occupied = False
        self.door = "closed"
        self.history.append(f"exit:{floor}")
        return self._handle("done", f"exit:{floor}")
