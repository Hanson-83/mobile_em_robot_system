from __future__ import annotations

from typing import Any

from app.core.errors import device_offline
from app.domain.dto import TempHumidityReading


class ClimateFake:
    def __init__(
        self,
        instrument_id: str,
        *,
        temperature_c: float = 22.5,
        humidity_pct: float = 45.0,
    ) -> None:
        self.instrument_id = instrument_id
        self.temperature_c = temperature_c
        self.humidity_pct = humidity_pct
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
        return {"ok": self._connected, "type": "climate_fake", "id": self.instrument_id}

    async def read_temp_humidity(self) -> TempHumidityReading:
        if not self._connected:
            raise device_offline(f"温湿度仪 {self.instrument_id} 离线")
        return TempHumidityReading(temperature_c=self.temperature_c, humidity_pct=self.humidity_pct)

    def inject(self, *, temperature_c: float | None = None, humidity_pct: float | None = None) -> None:
        if temperature_c is not None:
            self.temperature_c = temperature_c
        if humidity_pct is not None:
            self.humidity_pct = humidity_pct
