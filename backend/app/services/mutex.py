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
        self._holder_types: dict[str, list[str]] = {}
        self._guard = Lock()
        self._rank = {name: i for i, name in enumerate(LOCK_ORDER)}

    def try_acquire(
        self,
        resource_type: str,
        resource_id: str,
        holder: str,
        ttl_s: float | None = None,
        on_conflict: str = "queue",
    ) -> ResourceLock | None:
        """占用成功返回锁；queue 策略下冲突返回 None（由调度保持 Queued）。"""
        if resource_type not in LOCK_ORDER:
            raise DomainError("VALIDATION_ERROR", f"未知资源类型 {resource_type}")
        if on_conflict not in {"queue", "fail"}:
            raise DomainError("VALIDATION_ERROR", f"未知冲突策略 {on_conflict}")
        key = (resource_type, resource_id)
        now = time.time()
        ttl = ttl_s or self.default_ttl_s
        with self._guard:
            existing = self._locks.get(key)
            if existing and existing.expires_at <= now:
                del self._locks[key]
                existing = None
            if existing and existing.holder != holder:
                if on_conflict == "fail":
                    raise DomainError(
                        "CONFLICT_MUTEX",
                        f"{resource_type}:{resource_id} 被 {existing.holder} 占用",
                    )
                return None
            held_types = self._holder_types.get(holder, [])
            if held_types and self._rank[resource_type] < max(self._rank[t] for t in held_types):
                raise DomainError(
                    "VALIDATION_ERROR",
                    f"锁顺序须为 {' → '.join(LOCK_ORDER)}，已持 {held_types} 不能再取 {resource_type}",
                )
            lock = ResourceLock(resource_type, resource_id, holder, now + ttl)
            self._locks[key] = lock
            if resource_type not in held_types:
                self._holder_types.setdefault(holder, []).append(resource_type)
            return lock

    def acquire(
        self,
        resource_type: str,
        resource_id: str,
        holder: str,
        ttl_s: float | None = None,
        on_conflict: str = "fail",
    ) -> ResourceLock:
        got = self.try_acquire(
            resource_type,
            resource_id,
            holder,
            ttl_s=ttl_s,
            on_conflict=on_conflict,
        )
        if got is None:
            raise DomainError(
                "CONFLICT_MUTEX",
                f"{resource_type}:{resource_id} 排队中",
            )
        return got

    def release(self, resource_type: str, resource_id: str, holder: str) -> None:
        key = (resource_type, resource_id)
        with self._guard:
            existing = self._locks.get(key)
            if existing and existing.holder == holder:
                del self._locks[key]
                types = self._holder_types.get(holder, [])
                if resource_type in types:
                    types.remove(resource_type)
                if not types and holder in self._holder_types:
                    del self._holder_types[holder]
