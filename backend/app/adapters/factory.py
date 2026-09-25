"""按 YAML type 装配适配器。切换 Fake / 录制 / 厂商占位不改调度代码。"""

from __future__ import annotations

from app.adapters.fake_amr import AmrFake
from app.adapters.fake_elevator import ElevatorFake
from app.adapters.fake_instruments import AirflowFake, ClimateFake, ParticleFake
from app.adapters.placeholders import (
    AmrVendorX,
    ArmPlaceholder,
    DepthCameraPlaceholder,
    ElevatorVendorX,
    InstrumentVendorPlaceholder,
    ViablePlaceholder,
)
from app.adapters.recorded import AmrRecorded
from app.core.errors import validation_error


class DeviceRegistry:
    def __init__(self) -> None:
        self.amrs: dict = {}
        self.elevators: dict = {}
        self.instruments: dict = {}
        self.instrument_bindings: list[dict] = []
        self.robot_configs: dict[str, dict] = {}
        self.extras: dict = {}

    def amr(self, device_id: str):
        if device_id not in self.amrs:
            raise validation_error(f"未知机器人 {device_id}")
        return self.amrs[device_id]

    def elevator(self, device_id: str):
        if device_id not in self.elevators:
            raise validation_error(f"未知电梯 {device_id}")
        return self.elevators[device_id]

    def instrument(self, device_id: str):
        if device_id not in self.instruments:
            raise validation_error(f"未知仪表 {device_id}")
        return self.instruments[device_id]

    def instrument_for(self, robot_id: str, kind: str):
        for item in self.instrument_bindings:
            if item["robot_id"] == robot_id and item["kind"] == kind:
                return self.instruments[item["id"]]
        raise validation_error(f"机器人 {robot_id} 未绑定 {kind} 仪表")

    def all_devices(self) -> list:
        return [*self.amrs.values(), *self.elevators.values(), *self.instruments.values()]


class AdapterFactory:
    def build(self, config: dict) -> DeviceRegistry:
        registry = DeviceRegistry()
        for robot in config.get("robots") or []:
            adapter = self._build_amr(robot)
            registry.amrs[robot["id"]] = adapter
            registry.robot_configs[robot["id"]] = robot
        for item in config.get("instruments") or []:
            adapter = self._build_instrument(item)
            registry.instruments[item["id"]] = adapter
            registry.instrument_bindings.append(item)
        for item in config.get("elevators") or []:
            adapter = self._build_elevator(item)
            registry.elevators[item["id"]] = adapter
        return registry

    @staticmethod
    def _apply_session(adapter, spec: dict):
        timeout = spec.get("heartbeat_timeout_sec")
        if timeout is not None and hasattr(adapter, "configure_session"):
            adapter.configure_session(float(timeout))
        return adapter

    def _build_amr(self, spec: dict):
        kind = spec.get("adapter", "amr_fake")
        device_id = spec["id"]
        if kind == "amr_fake":
            return self._apply_session(AmrFake(device_id), spec)
        if kind == "amr_recorded":
            path = spec.get("recording")
            if not path:
                raise validation_error(f"{device_id} 缺少 recording")
            return self._apply_session(AmrRecorded(device_id, path), spec)
        if kind == "amr_vendor_x":
            return self._apply_session(AmrVendorX(device_id), spec)
        raise validation_error(f"未知 AMR 适配器 {kind}")

    def _build_elevator(self, spec: dict):
        kind = spec.get("adapter", "elevator_fake")
        device_id = spec["id"]
        floors = [int(item) for item in spec.get("floors") or [1, 2, 3]]
        if kind == "elevator_fake":
            return self._apply_session(ElevatorFake(device_id, floors=floors), spec)
        if kind == "elevator_vendor_x":
            return self._apply_session(ElevatorVendorX(device_id), spec)
        raise validation_error(f"未知电梯适配器 {kind}")

    def _build_instrument(self, spec: dict):
        kind = spec.get("adapter")
        device_id = spec["id"]
        access_mode = spec.get("access_mode", "direct")
        if access_mode not in {"direct", "via_edge_agent"}:
            raise validation_error(f"未知 access_mode {access_mode}")
        if kind == "particle_fake":
            return ParticleFake(device_id, access_mode=access_mode)
        if kind == "climate_fake":
            return ClimateFake(device_id, access_mode=access_mode)
        if kind == "airflow_fake":
            return AirflowFake(device_id, access_mode=access_mode)
        if kind == "particle_vendor_x":
            return InstrumentVendorPlaceholder(device_id, "particle_vendor_x", "粒子计数器")
        if kind == "climate_vendor_x":
            return InstrumentVendorPlaceholder(device_id, "climate_vendor_x", "温湿度")
        if kind == "airflow_vendor_x":
            return InstrumentVendorPlaceholder(device_id, "airflow_vendor_x", "风速")
        if kind == "viable_placeholder":
            return ViablePlaceholder(device_id)
        raise validation_error(f"未知仪表适配器 {kind}")


EXTENSION_ADAPTERS = {
    "viable_placeholder": ViablePlaceholder,
    "arm_placeholder": ArmPlaceholder,
    "depth_camera_placeholder": DepthCameraPlaceholder,
}
