"""领域 DTO / 适配边界对象。坐标系与单位在适配器边界转换完毕。"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Pose(BaseModel):
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    map_id: str | None = None
    floor: int | None = None


class RobotMode(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    CHARGING = "charging"
    FAULT = "fault"
    ESTOP = "estop"


class RobotStatus(BaseModel):
    robot_id: str
    estop: bool = False
    fault_code: str | None = None
    fault_msg: str | None = None
    mode: RobotMode = RobotMode.IDLE
    battery_pct: float | None = 100.0
    pose: Pose | None = None
    online: bool = True


class ElevatorStatus(BaseModel):
    elevator_id: str
    floor: int | None = None
    door: Literal["open", "closed", "unknown"] = "unknown"
    busy: bool = False
    online: bool = True
    fault_code: str | None = None


class CommandHandle(BaseModel):
    command_id: str
    status: Literal["pending", "succeeded", "failed", "cancelled"] = "succeeded"
    message: str | None = None


class ChannelReading(BaseModel):
    channel: str
    value: float
    unit: str = "count"


class TempHumidityReading(BaseModel):
    temperature_c: float
    humidity_pct: float


class AirSpeedReading(BaseModel):
    speed_mps: float


class Quality(StrEnum):
    GOOD = "good"
    UNCERTAIN = "uncertain"
    BAD = "bad"
    MISSING = "missing"


class MeasurementIn(BaseModel):
    task_id: str | None = None
    point_id: str | None = None
    robot_id: str | None = None
    device_id: str
    sample_id: str
    metric: str
    value: float | None = None
    unit: str
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    quality: Quality = Quality.GOOD
    client_request_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Measurement(MeasurementIn):
    id: str
    idempotency_key: str
    replay: bool = False


class TaskState(StrEnum):
    CREATED = "Created"
    QUEUED = "Queued"
    DISPATCHED = "Dispatched"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class SkillStep(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)


class TaskCreate(BaseModel):
    name: str
    robot_id: str | None = None
    skills: list[SkillStep] = Field(default_factory=list)
    client_request_id: str | None = None


class TaskInstance(BaseModel):
    id: str
    name: str
    robot_id: str | None = None
    skills: list[SkillStep] = Field(default_factory=list)
    state: TaskState = TaskState.CREATED
    reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Point(BaseModel):
    id: str
    map_id: str = "map-01"
    name: str
    pose: Pose = Field(default_factory=Pose)
    instrument_profile: str | None = None
    limits: dict[str, float] = Field(default_factory=dict)


class AlarmState(StrEnum):
    OPEN = "open"
    ACKED = "acked"
    CLOSED = "closed"


class Alarm(BaseModel):
    id: str
    rule_id: str = "limit"
    severity: Literal["info", "warning", "critical"] = "warning"
    state: AlarmState = AlarmState.OPEN
    message: str
    source: str | None = None
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ack_by: str | None = None


class ApprovalState(StrEnum):
    DRAFT = "Draft"
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    EXPIRED = "Expired"


class ApprovalRequest(BaseModel):
    id: str
    object_ref: str
    action: str
    state: ApprovalState = ApprovalState.PENDING
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Report(BaseModel):
    id: str
    task_ref: str
    file_uri: str
    format: Literal["html", "pdf"] = "html"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthBody(BaseModel):
    status: Literal["ok", "degraded"]
    service: str = "mer-gateway"


class ReadyBody(BaseModel):
    status: Literal["ok", "not_ready"]
    adapters: dict[str, str] = Field(default_factory=dict)
