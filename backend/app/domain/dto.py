"""适配层与领域共用的数据传输对象。单位在适配边界统一。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RobotMode = Literal["idle", "running", "charging", "fault", "estop", "offline"]
Quality = Literal["good", "uncertain", "bad", "missing"]


@dataclass
class Pose:
    x: float
    y: float
    theta: float = 0.0
    map_id: str | None = None

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "theta": self.theta, "map_id": self.map_id}


@dataclass
class RobotStatus:
    online: bool
    mode: str
    estop: bool = False
    fault_code: str | None = None
    fault_msg: str | None = None
    battery_pct: float | None = None
    pose: Pose | None = None

    def to_dict(self) -> dict:
        return {
            "online": self.online,
            "mode": self.mode,
            "estop": self.estop,
            "fault_code": self.fault_code,
            "fault_msg": self.fault_msg,
            "battery_pct": self.battery_pct,
            "pose": self.pose.to_dict() if self.pose else None,
        }


@dataclass
class ElevatorStatus:
    online: bool
    current_floor: int | None
    door: str
    moving: bool = False
    fault_code: str | None = None

    def to_dict(self) -> dict:
        return {
            "online": self.online,
            "current_floor": self.current_floor,
            "door": self.door,
            "moving": self.moving,
            "fault_code": self.fault_code,
        }


@dataclass
class CommandHandle:
    command_id: str
    status: str
    detail: str = ""


@dataclass
class ChannelReading:
    channel: str
    value: float
    unit: str = "counts"


@dataclass
class TempHumidityReading:
    temp_c: float
    humidity_rh: float


@dataclass
class AirSpeedReading:
    speed_mps: float
    unit: str = "m/s"


@dataclass
class DeviceHealth:
    ok: bool
    device_id: str
    adapter: str
    detail: str = ""
    extra: dict = field(default_factory=dict)
