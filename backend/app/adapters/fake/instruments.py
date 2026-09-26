from __future__ import annotations

import uuid
from typing import Any

from app.adapters.modbus_sim import ModbusHoldingSim
from app.core.errors import DomainError
from app.domain.models import AirSpeedReading, ChannelReading, CommandHandle, TempHumidityReading

PARTICLE_CHANNELS = ("0.1um", "0.5um", "1.0um", "5.0um")


class _BaseInst:
    def __init__(self, device_id: str, **_k: Any) -> None:
        self.device_id = device_id
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def _ensure(self) -> None:
        if not self._connected:
            raise DomainError("DEVICE_OFFLINE", f"仪表 {self.device_id} 离线")

    @staticmethod
    def _next_curve(curve: list[float], idx: int) -> tuple[float, int]:
        if not curve:
            return 0.0, idx
        i = min(idx, len(curve) - 1)
        return curve[i], idx + 1


class ParticleFake(_BaseInst):
    def __init__(
        self,
        device_id: str,
        *,
        exceed: bool = False,
        curve: list[float] | None = None,
        **kw: Any,
    ) -> None:
        super().__init__(device_id, **kw)
        self.exceed = exceed
        self._sampling = False
        self._curve = list(curve) if curve else None
        self._idx = 0
        self.unit_id = int(kw.get("unit_id", 1))
        self.bus = ModbusHoldingSim(self.unit_id)

    def health(self) -> dict[str, Any]:
        return {"id": self.device_id, "type": "particle_fake", "online": self._connected}

    def start_sample(self, params: dict[str, Any] | None = None) -> CommandHandle:
        self._ensure()
        self._sampling = True
        self.exceed = bool((params or {}).get("exceed", self.exceed))
        return CommandHandle(command_id=uuid.uuid4().hex[:12], status="succeeded")

    def stop_sample(self) -> None:
        self._ensure()
        self._sampling = False

    def inject(self, *, exceed: bool | None = None, curve: list[float] | None = None) -> None:
        if exceed is not None:
            self.exceed = exceed
        if curve is not None:
            self._curve = list(curve)
            self._idx = 0

    def read_channels(self) -> list[ChannelReading]:
        self._ensure()
        base = {"0.1um": 8000.0, "0.5um": 80.0, "1.0um": 20.0, "5.0um": 2.0}
        if self.exceed:
            base = {"0.1um": 20000.0, "0.5um": 1200.0, "1.0um": 200.0, "5.0um": 30.0}
        if self._curve:
            v05, self._idx = self._next_curve(self._curve, self._idx)
            base["0.5um"] = v05
        quality = "uncertain" if self.exceed else "good"
        values = [int(base[name]) for name in PARTICLE_CHANNELS]
        self.bus.write_registers(0, values)
        regs = self.bus.read_holding(0, len(PARTICLE_CHANNELS))
        return [
            ChannelReading(channel=name, value=float(regs[i]), unit="count/cf", quality=quality)
            for i, name in enumerate(PARTICLE_CHANNELS)
        ]


class ClimateFake(_BaseInst):
    def __init__(
        self,
        device_id: str,
        *,
        temp_curve: list[float] | None = None,
        exceed: bool = False,
        **kw: Any,
    ) -> None:
        super().__init__(device_id, **kw)
        self.exceed = exceed
        self._curve = list(temp_curve) if temp_curve else [22.0]
        self._idx = 0
        self.unit_id = int(kw.get("unit_id", 2))
        self.bus = ModbusHoldingSim(self.unit_id)

    def health(self) -> dict[str, Any]:
        return {"id": self.device_id, "type": "climate_fake", "online": self._connected}

    def inject(self, *, exceed: bool | None = None, temp_curve: list[float] | None = None) -> None:
        if exceed is not None:
            self.exceed = exceed
        if temp_curve is not None:
            self._curve = list(temp_curve)
            self._idx = 0

    def read_temp_humidity(self) -> TempHumidityReading:
        self._ensure()
        temp, self._idx = self._next_curve(self._curve, self._idx)
        if self.exceed:
            temp = 40.0
        q = "uncertain" if self.exceed else "good"
        humidity = 45.0
        self.bus.write_registers(0, [int(round(temp * 10)), int(round(humidity * 10))])
        regs = self.bus.read_holding(0, 2)
        return TempHumidityReading(
            temperature_c=regs[0] / 10,
            humidity_pct=regs[1] / 10,
            quality=q,
        )


class AirflowFake(_BaseInst):
    def __init__(
        self,
        device_id: str,
        *,
        speed_curve: list[float] | None = None,
        exceed: bool = False,
        **kw: Any,
    ) -> None:
        super().__init__(device_id, **kw)
        self.exceed = exceed
        self._curve = list(speed_curve) if speed_curve else [0.45]
        self._idx = 0
        self.unit_id = int(kw.get("unit_id", 3))
        self.bus = ModbusHoldingSim(self.unit_id)

    def health(self) -> dict[str, Any]:
        return {"id": self.device_id, "type": "airflow_fake", "online": self._connected}

    def inject(self, *, exceed: bool | None = None, speed_curve: list[float] | None = None) -> None:
        if exceed is not None:
            self.exceed = exceed
        if speed_curve is not None:
            self._curve = list(speed_curve)
            self._idx = 0

    def read_air_speed(self) -> AirSpeedReading:
        self._ensure()
        spd, self._idx = self._next_curve(self._curve, self._idx)
        if self.exceed:
            spd = 2.5
        q = "uncertain" if self.exceed else "good"
        self.bus.write_registers(0, [int(round(spd * 100))])
        regs = self.bus.read_holding(0, 1)
        return AirSpeedReading(speed_mps=regs[0] / 100, quality=q)
