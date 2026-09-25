"""运行配置：YAML 设备/特性 + 环境变量（密钥外置）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RobotConfig(BaseModel):
    id: str
    adapter: str
    endpoint: str | None = None
    model: str | None = None


class InstrumentConfig(BaseModel):
    id: str
    robot_id: str | None = None
    adapter: str
    access_mode: Literal["direct", "via_edge_agent"] = "direct"
    endpoint: str | None = None
    model: str | None = None
    unit: str | None = None
    precision: float | None = None
    channel_defs: list[str] = Field(default_factory=list)


class ElevatorConfig(BaseModel):
    id: str
    adapter: str
    endpoint: str | None = None
    floors: list[int] = Field(default_factory=list)
    model: str | None = None


class DevicesFile(BaseModel):
    robots: list[RobotConfig] = Field(default_factory=list)
    instruments: list[InstrumentConfig] = Field(default_factory=list)
    elevators: list[ElevatorConfig] = Field(default_factory=list)
    features: dict[str, Any] = Field(default_factory=dict)


class GatewayFeatures(BaseModel):
    rate_limit_per_min: int = 60


class SecurityFeatures(BaseModel):
    # 数值为占位，待用户确认后冻结（URS-SEC-002）
    password_min_len: int = 8
    session_ttl_min: int = 480


class MutexFeatures(BaseModel):
    ttl_s: int = 120
    acquire_wait_s: int = 30
    on_conflict: Literal["queue", "fail"] = "queue"


class MeasurementFeatures(BaseModel):
    write_missing: bool = False


class FeaturesFile(BaseModel):
    audit_trail: bool = False
    e_sign: bool = False
    elevator_skills: bool = True
    resource_mutex: Literal["simple"] = "simple"
    realtime_channel: Literal["websocket"] = "websocket"
    gateway: GatewayFeatures = Field(default_factory=GatewayFeatures)
    security: SecurityFeatures = Field(default_factory=SecurityFeatures)
    resource_mutex_config: MutexFeatures = Field(default_factory=MutexFeatures)
    measurement: MeasurementFeatures = Field(default_factory=MeasurementFeatures)
    on_fail: Literal["dock_charge", "goto_standby", "none"] = "none"
    low_battery_pct: float | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MER_", extra="ignore")

    devices_path: Path = Path("config/devices.example.yaml")
    features_path: Path = Path("config/features.example.yaml")
    env: Literal["dev", "prod"] = "dev"
    jwt_secret: str = "dev-only-change-me"
    bootstrap_admin_password: str = "admin"
    bootstrap_operator_password: str = "operator"
    bootstrap_viewer_password: str = "viewer"
    log_level: str = "INFO"
    repo_root: Path = Path(".")


WEAK_SECRETS = frozenset({"", "change-me", "dev-only-change-me", "admin", "operator", "viewer"})


def assert_runtime_secrets(settings: Settings) -> None:
    """生产环境禁止弱 JWT/口令；开发环境允许示例默认值。"""
    if settings.env != "prod":
        return
    if settings.jwt_secret in WEAK_SECRETS or len(settings.jwt_secret) < 16:
        raise RuntimeError("生产环境必须设置长度≥16 且非默认的 MER_JWT_SECRET")
    for name, value in (
        ("MER_BOOTSTRAP_ADMIN_PASSWORD", settings.bootstrap_admin_password),
        ("MER_BOOTSTRAP_OPERATOR_PASSWORD", settings.bootstrap_operator_password),
        ("MER_BOOTSTRAP_VIEWER_PASSWORD", settings.bootstrap_viewer_password),
    ):
        if value in WEAK_SECRETS or len(value) < 10:
            raise RuntimeError(f"生产环境必须设置长度≥10 且非默认的 {name}")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"配置必须是 mapping: {path}")
    return data


def load_devices(path: Path) -> DevicesFile:
    return DevicesFile.model_validate(load_yaml(path))


def load_features(path: Path) -> FeaturesFile:
    raw = load_yaml(path)
    # devices.example.yaml 也可内嵌 features{}
    if "audit_trail" not in raw and "features" in raw:
        raw = raw["features"]
    return FeaturesFile.model_validate(raw)


def resolve_path(settings: Settings, relative: Path) -> Path:
    if relative.is_absolute():
        return relative
    candidates = [
        settings.repo_root / relative,
        Path.cwd() / relative,
        Path.cwd().parent / relative,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return settings.repo_root / relative
