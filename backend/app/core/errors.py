"""统一领域错误与 Gateway 错误体（DS §4.2）。"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

ERROR_CODES = {
    "AUTH_REQUIRED": False,
    "FORBIDDEN": False,
    "VALIDATION_ERROR": False,
    "NOT_FOUND": False,
    "CONFLICT_MUTEX": True,
    "DEVICE_OFFLINE": True,
    "DEVICE_ESTOP": False,
    "APPROVAL_REQUIRED": False,
    "APPROVAL_REJECTED": False,
    "IDEMPOTENCY_REPLAY": False,
    "RATE_LIMITED": True,
    "INTERNAL_ERROR": True,
    "NOT_IMPLEMENTED": False,
}


class DomainError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool | None = None,
        details: Any | None = None,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = ERROR_CODES.get(code, False) if retryable is None else retryable
        self.details = details
        self.http_status = http_status or _default_status(code)

    def to_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details is not None:
            body["details"] = self.details
        return body


def _default_status(code: str) -> int:
    mapping = {
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
        "NOT_IMPLEMENTED": 501,
        "METHOD_NOT_ALLOWED": 405,
    }
    return mapping.get(code, 400)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=exc.to_body())

    @app.exception_handler(RequestValidationError)
    async def _validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        err = DomainError("VALIDATION_ERROR", "请求参数校验失败", details=exc.errors())
        return JSONResponse(status_code=err.http_status, content=err.to_body())

    @app.exception_handler(StarletteHTTPException)
    async def _http(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            err = DomainError("NOT_FOUND", str(exc.detail) if exc.detail else "资源不存在")
        elif exc.status_code == 405:
            err = DomainError("VALIDATION_ERROR", "方法不允许", http_status=405)
        elif exc.status_code == 401:
            err = DomainError("AUTH_REQUIRED", str(exc.detail))
        elif exc.status_code == 403:
            err = DomainError("FORBIDDEN", str(exc.detail))
        else:
            err = DomainError("INTERNAL_ERROR", str(exc.detail), http_status=exc.status_code)
        return JSONResponse(status_code=err.http_status, content=err.to_body())

    @app.exception_handler(Exception)
    async def _unhandled(_request: Request, exc: Exception) -> JSONResponse:
        err = DomainError("INTERNAL_ERROR", "内部错误")
        return JSONResponse(status_code=err.http_status, content=err.to_body())
