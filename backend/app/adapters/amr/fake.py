"""AmrFake：导航耗时、电量、故障/急停注入。不含 call/enter/exit_elevator。"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.adapters.amr.protocol import TelemetryCallback
from app.core.errors import device_estop, device_offline
from app.domain.dto import CommandHandle, Pose, RobotMode, RobotStatus


class AmrFake:
    def __init__(
        self,
        robot_id: str,
        *,
        delay_s: float = 0.01,
        battery_pct: float = 96.0,
        map_id: str = "map-01",
    ) -> None:
        self.robot_id = robot_id
        self.delay_s = delay_s
        self._connected = False
        self._status = RobotStatus(
            robot_id=robot_id,
            battery_pct=battery_pct,
            pose=Pose(x=0.0, y=0.0, map_id=map_id),
            mode=RobotMode.IDLE,
            online=False,
        )
        self._cb: TelemetryCallback | None = None
        self._last_command: str | None = None

    def _emit(self) -> None:
        if self._cb:
            self._cb(self._status.model_copy(deep=True))

    def _guard(self) -> None:
        if not self._connected or not self._status.online:
            raise device_offline(f"AMR {self.robot_id} 离线")
        if self._status.estop or self._status.mode == RobotMode.ESTOP:
            raise device_estop(f"AMR {self.robot_id} 急停中")
        if self._status.mode == RobotMode.FAULT:
            raise device_estop(f"AMR {self.robot_id} 故障中")

    async def connect(self) -> None:
        self._connected = True
        self._status.online = True
        if self._status.mode not in {RobotMode.FAULT, RobotMode.ESTOP}:
            self._status.mode = RobotMode.IDLE
        self._emit()

    async def disconnect(self) -> None:
        self._connected = False
        self._status.online = False
        self._emit()

    async def start(self) -> None:
        await self.connect()

    async def stop(self) -> None:
        await self.disconnect()

    async def health(self) -> dict[str, Any]:
        return {
            "ok": self._connected and self._status.online,
            "type": "amr_fake",
            "id": self.robot_id,
        }

    async def get_status(self) -> RobotStatus:
        return self._status.model_copy(deep=True)

    async def navigate_to(
        self,
        target: Pose | str,
        options: dict[str, Any] | None = None,
    ) -> CommandHandle:
        self._guard()
        self._status.mode = RobotMode.RUNNING
        self._emit()
        await asyncio.sleep(self.delay_s)
        self._guard()
        if isinstance(target, Pose):
            pose = target
        else:
            map_id = self._status.pose.map_id if self._status.pose else None
            pose = Pose(x=1.0, y=1.0, map_id=map_id)
            if options and "pose" in options:
                pose = Pose.model_validate(options["pose"])
        self._status.pose = pose
        self._status.mode = RobotMode.IDLE
        self._last_command = str(uuid.uuid4())
        self._emit()
        return CommandHandle(command_id=self._last_command, status="succeeded")

    async def cancel(self, command_id: str | None = None) -> None:
        if self._connected:
            self._status.mode = RobotMode.IDLE
            self._emit()

    async def dock_charge(self) -> CommandHandle:
        self._guard()
        await asyncio.sleep(self.delay_s)
        self._status.mode = RobotMode.CHARGING
        self._status.battery_pct = min(100.0, (self._status.battery_pct or 0) + 1.0)
        cid = str(uuid.uuid4())
        self._emit()
        return CommandHandle(command_id=cid, status="succeeded")

    def subscribe_telemetry(self, callback: TelemetryCallback) -> None:
        self._cb = callback

    def unsubscribe(self) -> None:
        self._cb = None

    def inject(
        self,
        *,
        estop: bool | None = None,
        fault_code: str | None = None,
        fault_msg: str | None = None,
        battery_pct: float | None = None,
        offline: bool | None = None,
    ) -> None:
        """Fake 故障注入（URS-ROB-009）。"""
        if estop is True:
            self._status.estop = True
            self._status.mode = RobotMode.ESTOP
        elif estop is False:
            self._status.estop = False
            if self._status.mode == RobotMode.ESTOP:
                self._status.mode = RobotMode.IDLE
        if fault_code is not None:
            self._status.fault_code = fault_code
            self._status.fault_msg = fault_msg or fault_code
            if fault_code:
                self._status.mode = RobotMode.FAULT
        if battery_pct is not None:
            self._status.battery_pct = battery_pct
        if offline is True:
            self._status.online = False
        elif offline is False:
            self._status.online = True
        self._emit()
