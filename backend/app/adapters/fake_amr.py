"""AmrFake：导航、电量、急停/故障注入。不含电梯方法。"""

from __future__ import annotations

from app.adapters.support import AdapterMixin
from app.core.errors import device_estop
from app.domain.dto import Pose, RobotStatus


class AmrFake(AdapterMixin):
    def __init__(self, device_id: str, adapter_type: str = "amr_fake") -> None:
        super().__init__(device_id, adapter_type)
        self.pose = Pose(0.0, 0.0, 0.0)
        self.battery_pct = 90.0
        self.estop = False
        self.fault_code: str | None = None
        self.fault_msg: str | None = None
        self.mode = "idle"
        self.force_offline = False
        self._subscribers: list = []
        self._active_command: str | None = None
        self.navigate_count = 0
        self.cancel_count = 0

    def get_status(self) -> RobotStatus:
        online = self._connected and not self.force_offline
        mode = self.mode
        if not online:
            mode = "offline"
        elif self.estop:
            mode = "estop"
        elif self.fault_code:
            mode = "fault"
        return RobotStatus(
            online=online,
            mode=mode,
            estop=self.estop,
            fault_code=self.fault_code,
            fault_msg=self.fault_msg,
            battery_pct=self.battery_pct,
            pose=Pose(self.pose.x, self.pose.y, self.pose.theta, self.pose.map_id),
        )

    def inject(
        self,
        *,
        estop: bool | None = None,
        fault_code: str | None = None,
        fault_msg: str | None = None,
        clear_fault: bool = False,
        battery_pct: float | None = None,
        online: bool | None = None,
        transient_failures: int | None = None,
    ) -> None:
        if estop is not None:
            self.estop = estop
            self.mode = "estop" if estop else "idle"
        if clear_fault:
            self.fault_code = None
            self.fault_msg = None
            if not self.estop:
                self.mode = "idle"
        if fault_code is not None:
            self.fault_code = fault_code
            self.fault_msg = fault_msg
            self.mode = "fault"
        if battery_pct is not None:
            self.battery_pct = battery_pct
        if online is not None:
            self.force_offline = not online
        if transient_failures is not None:
            self.transient_failures = transient_failures
        self._emit()

    def navigate_to(self, point_id: str | None = None, pose: Pose | None = None, options: dict | None = None):
        self._before_io()
        status = self.get_status()
        if status.estop or status.mode in {"estop", "fault"}:
            raise device_estop(status.fault_msg or "急停/故障，拒绝导航")
        if pose is not None:
            self.pose = Pose(pose.x, pose.y, pose.theta, pose.map_id)
        self.mode = "idle"
        self.battery_pct = max(0.0, self.battery_pct - 1.0)
        self.navigate_count += 1
        handle = self._handle("done", point_id or "pose")
        self._active_command = handle.command_id
        self._emit()
        return handle

    def cancel(self, command_id: str | None = None) -> None:
        self.cancel_count += 1
        self._active_command = None
        if self.mode == "running":
            self.mode = "idle"

    def dock_charge(self):
        self._before_io()
        status = self.get_status()
        if status.estop or status.mode in {"estop", "fault"}:
            raise device_estop("急停/故障，拒绝回充")
        self.mode = "charging"
        self.battery_pct = 100.0
        handle = self._handle("done", "dock_charge")
        self.mode = "idle"
        self._emit()
        return handle

    def subscribe_telemetry(self, callback) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback) -> None:
        self._subscribers = [item for item in self._subscribers if item is not callback]

    def _emit(self) -> None:
        status = self.get_status()
        for callback in list(self._subscribers):
            callback(status)
