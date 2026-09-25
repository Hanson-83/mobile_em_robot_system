"""简单互斥资源锁（M1 可测骨架；M2 编排接入）。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock

from app.core.errors import DomainError

LOCK_ORDER = ("zone", "elevator", "charger", "point")


@dataclass
class ResourceLock:
    resource_type: str
    resource_id: str
    holder: str
    expires_at: float


class MutexService:
    def __init__(self, default_ttl_s: float = 120.0) -> None:
        self.default_ttl_s = default_ttl_s
        self._locks: dict[tuple[str, str], ResourceLock] = {}
        self._guard = Lock()

    def acquire(
        self,
        resource_type: str,
        resource_id: str,
        holder: str,
        ttl_s: float | None = None,
        on_conflict: str = "fail",
    ) -> ResourceLock:
        if resource_type not in LOCK_ORDER:
            raise DomainError("VALIDATION_ERROR", f"未知资源类型 {resource_type}")
        key = (resource_type, resource_id)
        now = time.time()
        ttl = ttl_s or self.default_ttl_s
        with self._guard:
            existing = self._locks.get(key)
            if existing and existing.expires_at > now and existing.holder != holder:
                if on_conflict == "fail":
                    raise DomainError(
                        "CONFLICT_MUTEX",
                        f"{resource_type}:{resource_id} 被 {existing.holder} 占用",
                    )
                raise DomainError(
                    "CONFLICT_MUTEX",
                    "排队策略将在 M2 调度循环落地；M1 骨架遇冲突返回 CONFLICT_MUTEX",
                )
            lock = ResourceLock(resource_type, resource_id, holder, now + ttl)
            self._locks[key] = lock
            return lock

    def release(self, resource_type: str, resource_id: str, holder: str) -> None:
        key = (resource_type, resource_id)
        with self._guard:
            existing = self._locks.get(key)
            if existing and existing.holder == holder:
                del self._locks[key]
