"""领域 DTO（适配边界转换后的单位/坐标系）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


class RobotMode(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    CHARGING = "charging"
    FAULT = "fault"
    ESTOP = "estop"


@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    map_id: str | None = None
    floor: int | None = None


@dataclass
class RobotStatus:
    estop: bool = False
    fault_code: str | None = None
    fault_msg: str | None = None
    mode: RobotMode = RobotMode.IDLE
    battery_pct: float | None = 100.0
    pose: Pose | None = None
    online: bool = True


@dataclass
class ElevatorStatus:
    floor: int | None = None
    door: Literal["open", "closed", "unknown"] = "unknown"
    moving: bool = False
    online: bool = True
    fault_code: str | None = None


@dataclass
class CommandHandle:
    command_id: str
    status: Literal["accepted", "running", "succeeded", "failed"]
    message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelReading:
    channel: str
    value: float
    unit: str
    quality: Literal["good", "uncertain", "bad", "missing"] = "good"


@dataclass
class TempHumidityReading:
    temperature_c: float
    humidity_pct: float
    quality: Literal["good", "uncertain", "bad", "missing"] = "good"


@dataclass
class AirSpeedReading:
    speed_mps: float
    quality: Literal["good", "uncertain", "bad", "missing"] = "good"
