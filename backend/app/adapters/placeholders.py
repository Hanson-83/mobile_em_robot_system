"""厂商与远期适配器占位。连接时明确返回「等待用户资料」，不伪装已联通。"""

from __future__ import annotations

from app.adapters.support import AdapterMixin
from app.core.errors import AppError, device_offline
from app.domain.dto import (
    AirSpeedReading,
    ChannelReading,
    DeviceHealth,
    ElevatorStatus,
    RobotStatus,
    TempHumidityReading,
)


class VendorPlaceholder(AdapterMixin):
    def __init__(self, device_id: str, adapter_type: str, kind: str) -> None:
        super().__init__(device_id, adapter_type)
        self.kind = kind

    def connect(self) -> None:
        raise device_offline(f"{self.adapter_type} 占位：等待用户提供 {self.kind} API 文档后实现")

    def health(self) -> DeviceHealth:
        return DeviceHealth(
            ok=False,
            device_id=self.device_id,
            adapter=self.adapter_type,
            detail="vendor_api_not_provided",
        )

    def get_status(self) -> RobotStatus:
        return RobotStatus(online=False, mode="offline", fault_code="NOT_CONFIGURED", fault_msg=self.health().detail)


class ElevatorVendorX(VendorPlaceholder):
    def __init__(self, device_id: str) -> None:
        super().__init__(device_id, "elevator_vendor_x", "电梯")

    def get_elevator_status(self) -> ElevatorStatus:
        return ElevatorStatus(online=False, current_floor=None, door="unknown", fault_code="NOT_CONFIGURED")

    def get_status(self) -> ElevatorStatus:  # type: ignore[override]
        return self.get_elevator_status()

    def call_elevator(self, floor: int, options: dict | None = None):
        raise device_offline("电梯厂商适配器未实现")

    def enter_elevator(self, options: dict | None = None):
        raise device_offline("电梯厂商适配器未实现")

    def exit_elevator(self, options: dict | None = None):
        raise device_offline("电梯厂商适配器未实现")


class AmrVendorX(VendorPlaceholder):
    def __init__(self, device_id: str) -> None:
        super().__init__(device_id, "amr_vendor_x", "AMR")

    def navigate_to(self, point_id: str | None = None, pose=None, options: dict | None = None):
        raise device_offline("AMR 厂商适配器未实现")

    def cancel(self, command_id: str | None = None) -> None:
        return None

    def dock_charge(self):
        raise device_offline("AMR 厂商适配器未实现")

    def subscribe_telemetry(self, callback) -> None:
        return None

    def unsubscribe(self, callback) -> None:
        return None


class InstrumentVendorPlaceholder(VendorPlaceholder):
    def start_sample(self, params: dict | None = None):
        raise device_offline("仪表厂商适配器未实现")

    def stop_sample(self):
        raise device_offline("仪表厂商适配器未实现")

    def read_channels(self) -> list[ChannelReading]:
        raise device_offline("仪表厂商适配器未实现")

    def read_temp_humidity(self) -> TempHumidityReading:
        raise device_offline("仪表厂商适配器未实现")

    def read_air_speed(self) -> AirSpeedReading:
        raise device_offline("仪表厂商适配器未实现")


class ViablePlaceholder(InstrumentVendorPlaceholder):
    """浮游菌扩展占位（URS-INS-006，非 MVP 阻塞）。"""

    def __init__(self, device_id: str) -> None:
        super().__init__(device_id, "viable_placeholder", "浮游菌")


class ArmPlaceholder(VendorPlaceholder):
    """协作臂远期占位（URS-ROB-011）。"""

    def __init__(self, device_id: str) -> None:
        super().__init__(device_id, "arm_placeholder", "机械臂")


class DepthCameraPlaceholder(VendorPlaceholder):
    def __init__(self, device_id: str) -> None:
        super().__init__(device_id, "depth_camera_placeholder", "深度相机")


def not_implemented(kind: str) -> AppError:
    return AppError("DEVICE_OFFLINE", f"{kind} 占位未实现", retryable=True, status_code=503)
