from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any

from app.core.errors import DomainError
from app.domain.models import CommandHandle, Pose, RobotMode, RobotStatus

TelemetryCallback = Callable[[RobotStatus], None]


class AmrFake:
    """导航耗时、电量、故障/急停注入；不含电梯技能。"""

    def __init__(self, device_id: str, *, nav_delay_s: float = 0.02, **_kwargs: Any) -> None:
        self.device_id = device_id
        self.nav_delay_s = nav_delay_s
        self._connected = False
        self._status = RobotStatus(pose=Pose(), online=False)
        self._cb: TelemetryCallback | None = None
        self._last_cmd: str | None = None
        self._link_down = False

    def connect(self) -> None:
        if self._link_down:
            raise DomainError("DEVICE_OFFLINE", f"AMR {self.device_id} 链路断开")
        self._connected = True
        self._status.online = True

    def disconnect(self) -> None:
        self._connected = False
        self._status.online = False

    def health(self) -> dict[str, Any]:
        return {"id": self.device_id, "type": "amr_fake", "online": self._connected}

    def get_status(self) -> RobotStatus:
        self._ensure_online()
        return self._status

    def navigate_to(self, target: Pose | str, options: dict[str, Any] | None = None) -> CommandHandle:
        self._ensure_online()
        self._ensure_not_estop()
        delay = (options or {}).get("delay_s", self.nav_delay_s)
        time.sleep(float(delay))
        if isinstance(target, Pose):
            self._status.pose = target
        else:
            self._status.pose = Pose(x=1.0, y=1.0, map_id=str(target))
        self._status.mode = RobotMode.IDLE
        self._last_cmd = uuid.uuid4().hex[:12]
        self._emit()
        return CommandHandle(command_id=self._last_cmd, status="succeeded")

    def cancel(self, command_id: str | None = None) -> None:
        self._ensure_online()
        self._status.mode = RobotMode.IDLE

    def dock_charge(self) -> CommandHandle:
        self._ensure_online()
        self._ensure_not_estop()
        self._status.mode = RobotMode.CHARGING
        self._status.battery_pct = min(100.0, (self._status.battery_pct or 0) + 5)
        cid = uuid.uuid4().hex[:12]
        return CommandHandle(command_id=cid, status="succeeded")

    def subscribe_telemetry(self, callback: TelemetryCallback) -> None:
        self._cb = callback

    def unsubscribe(self) -> None:
        self._cb = None

    def inject(self, **kwargs: Any) -> None:
        """测试注入：estop / fault_code / battery_pct / offline。"""
        if "estop" in kwargs:
            self._status.estop = bool(kwargs["estop"])
            if self._status.estop:
                self._status.mode = RobotMode.ESTOP
        if "fault_code" in kwargs:
            self._status.fault_code = kwargs["fault_code"]
            self._status.fault_msg = kwargs.get("fault_msg", "injected")
            if self._status.fault_code:
                self._status.mode = RobotMode.FAULT
        if "battery_pct" in kwargs:
            self._status.battery_pct = float(kwargs["battery_pct"])
        if kwargs.get("offline"):
            self._status.online = False
            self._connected = False
        if "link_down" in kwargs:
            self._link_down = bool(kwargs["link_down"])
            if self._link_down:
                self._connected = False
                self._status.online = False
        self._emit()

    def _emit(self) -> None:
        if self._cb:
            self._cb(self._status)

    def _ensure_online(self) -> None:
        if not self._connected or not self._status.online:
            raise DomainError("DEVICE_OFFLINE", f"AMR {self.device_id} 离线")

    def _ensure_not_estop(self) -> None:
        if self._status.estop or self._status.mode in (RobotMode.ESTOP, RobotMode.FAULT):
            raise DomainError("DEVICE_ESTOP", "急停或故障中，拒绝下发导航/充电")
