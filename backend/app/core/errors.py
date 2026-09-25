"""领域错误与 Gateway 统一错误模型。"""

from __future__ import annotations


class AppError(Exception):
    """可映射为 HTTP 错误体的领域错误。"""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        status_code: int = 400,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code
        self.details = details or {}

    def to_body(self) -> dict:
        body: dict = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            body["details"] = self.details
        return body


def auth_required(message: str = "未鉴权") -> AppError:
    return AppError("AUTH_REQUIRED", message, retryable=False, status_code=401)


def forbidden(message: str = "无权限") -> AppError:
    return AppError("FORBIDDEN", message, retryable=False, status_code=403)


def not_found(message: str = "资源不存在") -> AppError:
    return AppError("NOT_FOUND", message, retryable=False, status_code=404)


def validation_error(message: str, details: dict | None = None) -> AppError:
    return AppError("VALIDATION_ERROR", message, retryable=False, status_code=422, details=details)


def conflict_mutex(message: str = "资源锁冲突") -> AppError:
    return AppError("CONFLICT_MUTEX", message, retryable=True, status_code=409)


def device_offline(message: str = "设备离线") -> AppError:
    return AppError("DEVICE_OFFLINE", message, retryable=True, status_code=503)


def device_estop(message: str = "设备急停或故障") -> AppError:
    return AppError("DEVICE_ESTOP", message, retryable=False, status_code=409)


def approval_required(message: str = "需要批准后方可生效", details: dict | None = None) -> AppError:
    return AppError("APPROVAL_REQUIRED", message, retryable=False, status_code=409, details=details)
