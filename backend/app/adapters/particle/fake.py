"""ParticleFake：可配置曲线与超限。"""

from __future__ import annotations

from typing import Any

from app.core.errors import device_offline
from app.domain.dto import ChannelReading


class ParticleFake:
    def __init__(
        self,
        instrument_id: str,
        *,
        channel_defs: list[str] | None = None,
        over_limit: bool = False,
    ) -> None:
        self.instrument_id = instrument_id
        self.channel_defs = channel_defs or ["0.5um", "5.0um"]
        self.over_limit = over_limit
        self._connected = False
        self._sampling = False
        self._scale = 1.0

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False
        self._sampling = False

    async def start(self) -> None:
        await self.connect()

    async def stop(self) -> None:
        await self.disconnect()

    async def health(self) -> dict[str, Any]:
        return {"ok": self._connected, "type": "particle_fake", "id": self.instrument_id}

    def _guard(self) -> None:
        if not self._connected:
            raise device_offline(f"粒子计数器 {self.instrument_id} 离线")

    async def start_sample(self, params: dict[str, Any] | None = None) -> None:
        self._guard()
        self._sampling = True
        if params and "scale" in params:
            self._scale = float(params["scale"])

    async def stop_sample(self) -> None:
        self._guard()
        self._sampling = False

    async def read_channels(self) -> list[ChannelReading]:
        self._guard()
        base = 1200.0 if self.over_limit else 80.0
        if not self._sampling:
            base *= 0.1
        return [
            ChannelReading(channel=name, value=base * self._scale * (i + 1), unit="count")
            for i, name in enumerate(self.channel_defs)
        ]

    def inject(self, *, over_limit: bool | None = None) -> None:
        if over_limit is not None:
            self.over_limit = over_limit
