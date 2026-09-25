"""统一领域错误模型（URS-API-002 / DS §4.2）。"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """跨模块使用的领域错误；Gateway 映射为统一 JSON。"""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details
        self.status_code = status_code

    def to_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            body["details"] = self.details
        return body


# 与 DS §4.2 错误码初稿对齐的工厂
def auth_required(message: str = "未鉴权") -> DomainError:
    return DomainError("AUTH_REQUIRED", message, status_code=401)


def forbidden(message: str = "无权限") -> DomainError:
    return DomainError("FORBIDDEN", message, status_code=403)


def validation_error(message: str, details: dict[str, Any] | None = None) -> DomainError:
    return DomainError("VALIDATION_ERROR", message, details=details, status_code=422)


def not_found(message: str = "资源不存在") -> DomainError:
    return DomainError("NOT_FOUND", message, status_code=404)


def conflict_mutex(message: str = "资源锁冲突") -> DomainError:
    return DomainError("CONFLICT_MUTEX", message, retryable=True, status_code=409)


def device_offline(message: str = "设备离线") -> DomainError:
    return DomainError("DEVICE_OFFLINE", message, retryable=True, status_code=503)


def device_estop(message: str = "急停中") -> DomainError:
    return DomainError("DEVICE_ESTOP", message, status_code=409)


def approval_required(message: str = "需批准") -> DomainError:
    return DomainError("APPROVAL_REQUIRED", message, status_code=409)


def rate_limited(message: str = "限流") -> DomainError:
    return DomainError("RATE_LIMITED", message, retryable=True, status_code=429)


def internal_error(message: str = "内部错误") -> DomainError:
    return DomainError("INTERNAL_ERROR", message, retryable=True, status_code=500)


ERROR_STATUS: dict[str, int] = {
    "AUTH_REQUIRED": 401,
    "FORBIDDEN": 403,
    "VALIDATION_ERROR": 422,
    "NOT_FOUND": 404,
    "CONFLICT_MUTEX": 409,
    "DEVICE_OFFLINE": 503,
    "DEVICE_ESTOP": 409,
    "APPROVAL_REQUIRED": 409,
    "APPROVAL_REJECTED": 409,
    "IDEMPOTENCY_REPLAY": 200,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
}
