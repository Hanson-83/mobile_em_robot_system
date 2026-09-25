"""简单互斥资源锁（scheme §5.1）。完整编排在 M2 接入。"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.core.config import MutexFeatures
from app.core.errors import conflict_mutex, validation_error

RESOURCE_ORDER = ("zone", "elevator", "charger", "point")


@dataclass
class LockRecord:
    resource_type: str
    resource_id: str
    holder: str
    expires_at: float


class LockService:
    def __init__(self, features: MutexFeatures | None = None) -> None:
        self.features = features or MutexFeatures()
        self._locks: dict[tuple[str, str], LockRecord] = {}

    def _purge(self) -> None:
        now = time.monotonic()
        expired = [k for k, v in self._locks.items() if v.expires_at <= now]
        for k in expired:
            del self._locks[k]

    def acquire(
        self,
        resource_type: str,
        resource_id: str,
        holder: str,
        ttl: float | None = None,
    ) -> LockRecord:
        if resource_type not in RESOURCE_ORDER:
            raise validation_error(f"未知资源类型: {resource_type}")
        self._purge()
        key = (resource_type, resource_id)
        existing = self._locks.get(key)
        if existing and existing.holder != holder:
            if self.features.on_conflict == "fail":
                raise conflict_mutex(
                    f"{resource_type}:{resource_id} 被 {existing.holder} 占用"
                )
            raise conflict_mutex(
                f"{resource_type}:{resource_id} 被 {existing.holder} 占用（queue 策略：M1 进程内立即返回冲突）"
            )
        record = LockRecord(
            resource_type=resource_type,
            resource_id=resource_id,
            holder=holder,
            expires_at=time.monotonic() + (ttl if ttl is not None else self.features.ttl_s),
        )
        self._locks[key] = record
        return record

    def release(self, resource_type: str, resource_id: str, holder: str) -> None:
        key = (resource_type, resource_id)
        existing = self._locks.get(key)
        if existing and existing.holder == holder:
            del self._locks[key]

    def holder_of(self, resource_type: str, resource_id: str) -> str | None:
        self._purge()
        rec = self._locks.get((resource_type, resource_id))
        return rec.holder if rec else None
