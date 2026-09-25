"""AdapterFactory：按 YAML type 装配；MVP access_mode=direct。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.adapters.fake import AirflowFake, AmrFake, ClimateFake, ElevatorFake, ParticleFake
from app.adapters.vendor_stubs import AmrVendorX, ElevatorVendorX, ParticleVendorX
from app.core.config import DevicesConfig
from app.core.errors import DomainError

AMR_TYPES = {
    "amr_fake": AmrFake,
    "amr_vendor_x": AmrVendorX,
}
ELEV_TYPES = {
    "elevator_fake": ElevatorFake,
    "elevator_vendor_x": ElevatorVendorX,
}
INST_TYPES = {
    "particle_fake": ParticleFake,
    "climate_fake": ClimateFake,
    "airflow_fake": AirflowFake,
    "particle_vendor_x": ParticleVendorX,
}


@dataclass
class DeviceRegistry:
    robots: dict[str, Any] = field(default_factory=dict)
    instruments: dict[str, Any] = field(default_factory=dict)
    elevators: dict[str, Any] = field(default_factory=dict)

    def start_all(self) -> None:
        for bucket in (self.robots, self.instruments, self.elevators):
            for dev in bucket.values():
                connect = getattr(dev, "connect", None)
                if connect:
                    connect()

    def stop_all(self) -> None:
        for bucket in (self.robots, self.instruments, self.elevators):
            for dev in bucket.values():
                disconnect = getattr(dev, "disconnect", None)
                if disconnect:
                    disconnect()

    def health(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for bucket in (self.robots, self.instruments, self.elevators):
            for dev in bucket.values():
                out.append(dev.health())
        return out


class AdapterFactory:
    @staticmethod
    def build(cfg: DevicesConfig) -> DeviceRegistry:
        reg = DeviceRegistry()
        for r in cfg.robots:
            cls = AMR_TYPES.get(r.adapter)
            if not cls:
                raise DomainError("VALIDATION_ERROR", f"未知 AMR adapter: {r.adapter}")
            reg.robots[r.id] = cls(r.id, endpoint=r.endpoint, model=r.model, **r.options)
        for e in cfg.elevators:
            cls = ELEV_TYPES.get(e.adapter)
            if not cls:
                raise DomainError("VALIDATION_ERROR", f"未知 Elevator adapter: {e.adapter}")
            reg.elevators[e.id] = cls(
                e.id, floors=e.floors, endpoint=e.endpoint, model=e.model, **e.options
            )
        for i in cfg.instruments:
            if i.access_mode != "direct":
                # 预留 via_edge_agent；MVP 拒绝作为默认验收路径
                raise DomainError(
                    "VALIDATION_ERROR",
                    f"MVP 仅支持 access_mode=direct（{i.id}={i.access_mode}）",
                )
            cls = INST_TYPES.get(i.adapter)
            if not cls:
                raise DomainError("VALIDATION_ERROR", f"未知仪表 adapter: {i.adapter}")
            reg.instruments[i.id] = cls(i.id, endpoint=i.endpoint, model=i.model, **i.options)
        return reg
