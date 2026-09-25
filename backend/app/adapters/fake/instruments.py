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


class ParticleFake(_BaseInst):
    def __init__(self, device_id: str, *, exceed: bool = False, **kw: Any) -> None:
        super().__init__(device_id, **kw)
        self.exceed = exceed
        self._sampling = False

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

    def read_channels(self) -> list[ChannelReading]:
        self._ensure()
        v05 = 1200.0 if self.exceed else 80.0
        v50 = 30.0 if self.exceed else 2.0
        return [
            ChannelReading(channel="0.5um", value=v05, unit="count/cf"),
            ChannelReading(channel="5.0um", value=v50, unit="count/cf"),
        ]


class ClimateFake(_BaseInst):
    def health(self) -> dict[str, Any]:
        return {"id": self.device_id, "type": "climate_fake", "online": self._connected}

    def read_temp_humidity(self) -> TempHumidityReading:
        self._ensure()
        return TempHumidityReading(temperature_c=22.0, humidity_pct=45.0)


class AirflowFake(_BaseInst):
    def health(self) -> dict[str, Any]:
        return {"id": self.device_id, "type": "airflow_fake", "online": self._connected}

    def read_air_speed(self) -> AirSpeedReading:
        self._ensure()
        return AirSpeedReading(speed_mps=0.45)
