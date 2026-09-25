"""进程内共享状态，避免循环导入。"""

from __future__ import annotations

from app.adapters.factory import DeviceRegistry
from app.core.config import FeaturesConfig, Settings
from app.core.rate_limit import RateLimiter
from app.services.mutex import MutexService

settings = Settings()
limiter = RateLimiter(per_min=settings.gateway_rate_limit_per_min)
registry: DeviceRegistry | None = None
features = FeaturesConfig()
mutex = MutexService()


def get_secret() -> str:
    return settings.mer_secret


def get_limiter() -> RateLimiter:
    return limiter


def get_registry() -> DeviceRegistry:
    assert registry is not None
    return registry
