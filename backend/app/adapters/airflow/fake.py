from __future__ import annotations

from typing import Any

from app.core.errors import device_offline
from app.domain.dto import AirSpeedReading


class AirflowFake:
    def __init__(self, instrument_id: str, *, speed_mps: float = 0.45) -> None:
        self.instrument_id = instrument_id
        self.speed_mps = speed_mps
        self._connected = False

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def start(self) -> None:
        await self.connect()

    async def stop(self) -> None:
        await self.disconnect()

    async def health(self) -> dict[str, Any]:
        return {"ok": self._connected, "type": "airflow_fake", "id": self.instrument_id}

    async def read_air_speed(self) -> AirSpeedReading:
        if not self._connected:
            raise device_offline(f"风速仪 {self.instrument_id} 离线")
        return AirSpeedReading(speed_mps=self.speed_mps)

    def inject(self, *, speed_mps: float | None = None) -> None:
        if speed_mps is not None:
            self.speed_mps = speed_mps
