from __future__ import annotations

import uuid
from typing import Any

from app.core.errors import DomainError
from app.domain.models import AirSpeedReading, ChannelReading, CommandHandle, TempHumidityReading


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
        if self._curve:
            v05, self._idx = self._next_curve(self._curve, self._idx)
        else:
            v05 = 1200.0 if self.exceed else 80.0
        v50 = 30.0 if self.exceed else 2.0
        quality = "good" if not self.exceed else "uncertain"
        return [
            ChannelReading(channel="0.5um", value=v05, unit="count/cf", quality=quality),
            ChannelReading(channel="5.0um", value=v50, unit="count/cf", quality=quality),
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
        return TempHumidityReading(temperature_c=temp, humidity_pct=45.0, quality=q)


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
        return AirSpeedReading(speed_mps=spd, quality=q)
