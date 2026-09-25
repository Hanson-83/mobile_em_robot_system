"""YAML + 环境变量配置（Twelve-Factor）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mer_env: str = "dev"
    mer_secret: str = "change-me-dev-only"
    mer_config_dir: Path = Path("../config")
    gateway_rate_limit_per_min: int = 60
    cors_origins: str = "http://localhost:5173"


class RobotCfg(BaseModel):
    id: str
    adapter: str
    endpoint: str | None = None
    model: str | None = None
    name: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class InstrumentCfg(BaseModel):
    id: str
    adapter: str
    robot_id: str | None = None
    access_mode: Literal["direct", "via_edge_agent"] = "direct"
    endpoint: str | None = None
    model: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ElevatorCfg(BaseModel):
    id: str
    adapter: str
    endpoint: str | None = None
    floors: list[int] = Field(default_factory=list)
    model: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class DevicesConfig(BaseModel):
    robots: list[RobotCfg] = Field(default_factory=list)
    instruments: list[InstrumentCfg] = Field(default_factory=list)
    elevators: list[ElevatorCfg] = Field(default_factory=list)
    features: dict[str, Any] = Field(default_factory=dict)


class FeaturesConfig(BaseModel):
    audit_trail: bool = False
    e_sign: bool = False
    elevator_skills: bool = True
    resource_mutex: Literal["simple"] = "simple"
    realtime_channel: Literal["websocket"] = "websocket"
    write_missing: bool = False


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML 根须为 mapping: {path}")
    return data


def load_devices(config_dir: Path, filename: str = "devices.example.yaml") -> DevicesConfig:
    path = config_dir / filename
    if not path.exists():
        # 仓库布局：backend/ 运行时 config 在上一级
        alt = config_dir.parent / "config" / filename
        path = alt if alt.exists() else path
    return DevicesConfig.model_validate(load_yaml(path))


def load_features(config_dir: Path, filename: str = "features.example.yaml") -> FeaturesConfig:
    path = config_dir / filename
    if not path.exists():
        alt = config_dir.parent / "config" / filename
        path = alt if alt.exists() else path
    if not path.exists():
        return FeaturesConfig()
    return FeaturesConfig.model_validate(load_yaml(path))


def resolve_config_dir(settings: Settings | None = None) -> Path:
    s = settings or Settings()
    cand = s.mer_config_dir
    if cand.exists():
        return cand
    repo_config = Path(__file__).resolve().parents[3] / "config"
    if repo_config.exists():
        return repo_config
    return cand
