"""特性开关、指标、实时事件、幂等键与重试。"""

from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime

from app.adapters.repository import Repository
from app.core.errors import AppError
from app.core.logging import get_logger, request_id_var

log = get_logger("mer.support")


class FeatureService:
    FLAG_KEYS = {
        "audit_trail",
        "e_sign",
        "elevator_skills",
        "resource_mutex",
        "realtime_channel",
        "resource_mutex_on_conflict",
        "measurement_write_missing",
        "fail_on_disconnect",
        "low_battery_pct",
        "auto_backup_interval_minutes",
    }

    def __init__(self, repo: Repository, defaults: dict, settings) -> None:
        self.repo = repo
        self.defaults = {key: defaults.get(key) for key in self.FLAG_KEYS if key in defaults}
        self.settings = settings

    def snapshot(self) -> dict:
        merged = {
            "audit_trail": False,
            "e_sign": False,
            "elevator_skills": True,
            "resource_mutex": "simple",
            "realtime_channel": "websocket",
            "resource_mutex_on_conflict": "queue",
            "measurement_write_missing": False,
            "fail_on_disconnect": True,
            "low_battery_pct": self.settings.low_battery_pct,
            "auto_backup_interval_minutes": 60,
        }
        merged.update(self.defaults)
        overlay = self.repo.get_kv("features") or {}
        merged.update({key: overlay[key] for key in overlay if key in self.FLAG_KEYS})
        if "low_battery_pct" not in overlay and "low_battery_pct" not in self.defaults:
            merged["low_battery_pct"] = self.settings.low_battery_pct
        return merged

    def update(self, patch: dict) -> dict:
        unknown = set(patch) - self.FLAG_KEYS
        if unknown:
            raise AppError("VALIDATION_ERROR", f"未知开关 {sorted(unknown)}", status_code=422)
        current = self.repo.get_kv("features") or {}
        current.update(patch)
        self.repo.put_kv("features", current)
        return self.snapshot()


class Metrics:
    def __init__(self) -> None:
        self.dispatch_latency_ms: list[float] = []
        self.command_ok = 0
        self.command_fail = 0
        self.mutex_wait_ms: list[float] = []
        self.requests = 0
        self.errors = 0
        self.task_depth = 0

    def snapshot(self, online: int) -> dict:
        def avg(values: list[float]) -> float:
            return round(sum(values) / len(values), 3) if values else 0.0

        ratio = 1.0
        total = self.command_ok + self.command_fail
        if total:
            ratio = round(self.command_ok / total, 4)
        error_rate = round(self.errors / self.requests, 4) if self.requests else 0.0
        return {
            "scheduler.dispatch_latency_ms": avg(self.dispatch_latency_ms),
            "adapter.command_success_ratio": ratio,
            "adapter.online": online,
            "queue.task_depth": self.task_depth,
            "mutex.wait_ms": avg(self.mutex_wait_ms),
            "gateway.request_rate": self.requests,
            "gateway.error_rate": error_rate,
        }


class RealtimeHub:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self._subscribers: list = []

    def subscribe(self):
        import asyncio

        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def publish(self, topic: str, payload: dict) -> None:
        event = {
            "id": hashlib.sha1(f"{topic}|{time.time_ns()}|{len(self.events)}".encode()).hexdigest()[:16],
            "topic": topic,
            "payload": payload,
            "ts": datetime.now(UTC).isoformat(),
        }
        self.events.append(event)
        if len(self.events) > 200:
            self.events = self.events[-200:]
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except Exception:
                log.warning("realtime subscriber dropped")


class RateLimiter:
    def __init__(self, limit_per_min: int) -> None:
        self.limit = limit_per_min
        self._hits: dict[str, list[float]] = {}

    def check(self, key: str) -> None:
        now = time.monotonic()
        window = [item for item in self._hits.get(key, []) if now - item < 60]
        if len(window) >= self.limit:
            raise AppError("RATE_LIMITED", "超过每分钟请求限制", retryable=True, status_code=429)
        window.append(now)
        self._hits[key] = window


def idempotency_key(
    *,
    client_request_id: str | None,
    device_id: str,
    sample_id: str,
    ts_iso: str,
) -> str:
    if client_request_id:
        return client_request_id
    raw = f"{device_id}|{sample_id}|{ts_iso}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def audit(
    repo: Repository,
    features: FeatureService,
    *,
    actor: str,
    action: str,
    object_ref: str,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    if not features.snapshot().get("audit_trail"):
        return
    import json

    repo.append_audit(
        actor=actor,
        action=action,
        object_ref=object_ref,
        before_json=json.dumps(before or {}, ensure_ascii=False),
        after_json=json.dumps(after or {}, ensure_ascii=False),
        request_id=request_id_var.get(),
    )
    log.info("audit %s %s", action, object_ref)


def read_with_retry(fn, attempts: int):
    """适配层读失败退避。fast 模式下不睡眠，仍遵守次数上限。"""
    retried = False
    last: Exception | None = None
    for index in range(attempts):
        try:
            return fn(), retried
        except AppError as exc:
            last = exc
            if not exc.retryable or index == attempts - 1:
                raise
            retried = True
    if last:
        raise last
    raise AppError("INTERNAL_ERROR", "重试失败", retryable=True, status_code=500)
