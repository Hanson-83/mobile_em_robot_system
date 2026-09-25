"""AdapterFactory：按 YAML type 装配。MVP 仅 access_mode=direct。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.adapters.airflow.fake import AirflowFake
from app.adapters.amr.fake import AmrFake
from app.adapters.climate.fake import ClimateFake
from app.adapters.elevator.fake import ElevatorFake
from app.adapters.particle.fake import ParticleFake
from app.core.config import DevicesFile, InstrumentConfig
from app.core.errors import validation_error

log = logging.getLogger("mer.adapters")

VENDOR_TYPES = {
    "amr_vendor_x",
    "elevator_vendor_x",
    "particle_vendor_x",
    "climate_vendor_x",
    "airflow_vendor_x",
}


@dataclass
class DeviceRegistry:
    robots: dict[str, Any] = field(default_factory=dict)
    elevators: dict[str, Any] = field(default_factory=dict)
    instruments: dict[str, Any] = field(default_factory=dict)

    def all_adapters(self) -> list[Any]:
        return [*self.robots.values(), *self.elevators.values(), *self.instruments.values()]


class AdapterFactory:
    @staticmethod
    def build(devices: DevicesFile) -> DeviceRegistry:
        registry = DeviceRegistry()
        for robot in devices.robots:
            registry.robots[robot.id] = AdapterFactory._build_amr(robot.id, robot.adapter)
        for elev in devices.elevators:
            registry.elevators[elev.id] = AdapterFactory._build_elevator(
                elev.id, elev.adapter, elev.floors
            )
        for inst in devices.instruments:
            AdapterFactory._check_access_mode(inst)
            registry.instruments[inst.id] = AdapterFactory._build_instrument(inst)
        return registry

    @staticmethod
    def _check_access_mode(inst: InstrumentConfig) -> None:
        if inst.access_mode == "via_edge_agent":
            log.warning(
                "access_mode=via_edge_agent 为演进占位，MVP 不装配边端代理: %s",
                inst.id,
            )
            raise validation_error(
                "MVP 仅支持 access_mode=direct；via_edge_agent 为演进占位",
                details={"instrument_id": inst.id},
            )

    @staticmethod
    def _reject_vendor(adapter: str) -> None:
        if adapter in VENDOR_TYPES:
            raise validation_error(
                f"适配器 {adapter} 为真实设备占位，等待用户 API 文档",
                details={"adapter": adapter},
            )

    @staticmethod
    def _build_amr(robot_id: str, adapter: str) -> AmrFake:
        AdapterFactory._reject_vendor(adapter)
        if adapter != "amr_fake":
            raise validation_error(f"未知 AMR 适配器: {adapter}")
        return AmrFake(robot_id)

    @staticmethod
    def _build_elevator(elevator_id: str, adapter: str, floors: list[int]) -> ElevatorFake:
        AdapterFactory._reject_vendor(adapter)
        if adapter != "elevator_fake":
            raise validation_error(f"未知电梯适配器: {adapter}")
        return ElevatorFake(elevator_id, floors=floors)

    @staticmethod
    def _build_instrument(inst: InstrumentConfig) -> Any:
        AdapterFactory._reject_vendor(inst.adapter)
        if inst.adapter == "particle_fake":
            return ParticleFake(inst.id, channel_defs=inst.channel_defs or None)
        if inst.adapter == "climate_fake":
            return ClimateFake(inst.id)
        if inst.adapter == "airflow_fake":
            return AirflowFake(inst.id)
        raise validation_error(f"未知仪表适配器: {inst.adapter}")
