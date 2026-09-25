"""粒子 / 温湿度 / 风速 Fake。曲线与超限由注入控制。"""

from __future__ import annotations

from app.adapters.support import AdapterMixin
from app.domain.dto import AirSpeedReading, ChannelReading, TempHumidityReading


class ParticleFake(AdapterMixin):
    def __init__(self, device_id: str, adapter_type: str = "particle_fake", access_mode: str = "direct") -> None:
        super().__init__(device_id, adapter_type, access_mode)
        self.channels = {"0.5": 100.0, "5.0": 5.0}
        self.sampling = False

    def inject_channels(self, channels: dict[str, float]) -> None:
        self.channels = {key: float(value) for key, value in channels.items()}

    def start_sample(self, params: dict | None = None):
        self._ensure()
        self.sampling = True
        return self._handle("done", "start_sample")

    def stop_sample(self):
        self._ensure()
        self.sampling = False
        return self._handle("done", "stop_sample")

    def read_channels(self) -> list[ChannelReading]:
        self._before_io()
        return [ChannelReading(channel=name, value=value) for name, value in self.channels.items()]


class ClimateFake(AdapterMixin):
    def __init__(self, device_id: str, adapter_type: str = "climate_fake", access_mode: str = "direct") -> None:
        super().__init__(device_id, adapter_type, access_mode)
        self.temp_c = 22.0
        self.humidity_rh = 45.0

    def inject(self, *, temp_c: float | None = None, humidity_rh: float | None = None) -> None:
        if temp_c is not None:
            self.temp_c = temp_c
        if humidity_rh is not None:
            self.humidity_rh = humidity_rh

    def read_temp_humidity(self) -> TempHumidityReading:
        self._before_io()
        return TempHumidityReading(temp_c=self.temp_c, humidity_rh=self.humidity_rh)


class AirflowFake(AdapterMixin):
    def __init__(self, device_id: str, adapter_type: str = "airflow_fake", access_mode: str = "direct") -> None:
        super().__init__(device_id, adapter_type, access_mode)
        self.speed_mps = 0.2

    def inject(self, speed_mps: float) -> None:
        self.speed_mps = speed_mps

    def read_air_speed(self) -> AirSpeedReading:
        self._before_io()
        return AirSpeedReading(speed_mps=self.speed_mps)
