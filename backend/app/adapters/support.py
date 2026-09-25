"""适配器公共辅助：命令号、瞬断注入、生命周期。"""

from __future__ import annotations

import time
import uuid

from app.core.errors import AppError, device_offline
from app.domain.dto import CommandHandle, DeviceHealth


class AdapterMixin:
    def __init__(self, device_id: str, adapter_type: str, access_mode: str = "direct") -> None:
        self.device_id = device_id
        self.adapter_type = adapter_type
        self.access_mode = access_mode
        self._started = False
        self._connected = False
        self.transient_failures = 0
        self.attempts = 0
        self._heartbeat_timeout_sec = 0.0
        self._last_heartbeat = time.monotonic()

    def configure_session(self, heartbeat_timeout_sec: float) -> None:
        """心跳超时。0 表示不启用，避免未配置的 Fake 被误判离线。"""
        self._heartbeat_timeout_sec = max(0.0, float(heartbeat_timeout_sec))
        self._last_heartbeat = time.monotonic()

    def heartbeat(self) -> None:
        """会话心跳。超时后再次心跳视为重连。"""
        self._last_heartbeat = time.monotonic()
        self._connected = True

    def _heartbeat_expired(self) -> bool:
        if self._heartbeat_timeout_sec <= 0 or not self._connected:
            return False
        return time.monotonic() - self._last_heartbeat > self._heartbeat_timeout_sec

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def start(self) -> None:
        self.connect()
        self._started = True

    def stop(self) -> None:
        self._started = False
        self.disconnect()

    def health(self) -> DeviceHealth:
        expired = self._heartbeat_expired()
        ok = self._connected and not expired
        if expired:
            detail = "heartbeat timeout"
        elif self._connected:
            detail = "ok"
        else:
            detail = "disconnected"
        return DeviceHealth(
            ok=ok,
            device_id=self.device_id,
            adapter=self.adapter_type,
            detail=detail,
            extra={"access_mode": self.access_mode, "heartbeat_timeout_sec": self._heartbeat_timeout_sec},
        )

    def _ensure(self) -> None:
        if not self._connected:
            raise device_offline(f"{self.device_id} 未连接")

    def _before_io(self) -> None:
        self._ensure()
        self.attempts += 1
        if self.transient_failures > 0:
            self.transient_failures -= 1
            raise AppError("DEVICE_OFFLINE", f"{self.device_id} 瞬时读失败", retryable=True, status_code=503)

    def _handle(self, status: str, detail: str = "") -> CommandHandle:
        return CommandHandle(command_id=uuid.uuid4().hex[:12], status=status, detail=detail)
