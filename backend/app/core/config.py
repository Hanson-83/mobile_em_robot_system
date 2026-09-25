"""运行配置。密钥与环境差异只来自环境变量或显式构造。"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def repo_root() -> Path:
    """仓库根目录：backend/app/core/config.py → 上溯四级。"""
    return Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MER_", extra="ignore")

    env: str = "development"
    secret_key: str = "dev-only-change-me"
    database_url: str = ""
    devices_config: str = ""
    features_config: str = ""
    reports_dir: str = ""
    backup_dir: str = ""
    config_dir: str = ""
    dev_seed: bool = True
    dev_api_token: str = "dev-api-token-change-me"
    allow_dev_secret: bool = True
    fast_retry: bool = True
    auto_bootstrap: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    password_min_len: int = 8
    session_ttl_min: int = 480
    rate_limit_per_min: int = 60
    low_battery_pct: float = 20.0
    lock_ttl_sec: int = 120
    approval_ttl_hours: int = 72
    adapter_max_attempts: int = 3

    def model_post_init(self, __context: object) -> None:
        root = repo_root()
        if not self.database_url:
            self.database_url = f"sqlite:///{root / 'var' / 'mer.db'}"
        if not self.devices_config:
            self.devices_config = str(root / "config" / "devices.example.yaml")
        if not self.features_config:
            self.features_config = str(root / "config" / "features.example.yaml")
        if not self.reports_dir:
            self.reports_dir = str(root / "var" / "reports")
        if not self.backup_dir:
            self.backup_dir = str(root / "var" / "backups")
        if not self.config_dir:
            self.config_dir = str(root / "config")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
