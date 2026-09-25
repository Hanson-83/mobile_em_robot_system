"""API Gateway 进程入口。"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.adapters.factory import AdapterFactory
from app.adapters.repository import Repository
from app.api.routes import register_routes
from app.core.config import Settings
from app.core.errors import AppError
from app.core.logging import get_logger, request_id_var, setup_logging
from app.core.security import decode_token, hash_token
from app.services.backup import maybe_auto_backup
from app.services.bootstrap import apply_schema, load_yaml, seed
from app.services.scheduler import Scheduler
from app.services.support import FeatureService, Metrics, RateLimiter, RealtimeHub

log = get_logger("mer.gateway")


class Runtime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.metrics = Metrics()
        self.hub = RealtimeHub()
        self.limiter = RateLimiter(settings.rate_limit_per_min)
        self.engine = self._make_engine(settings.database_url)
        apply_schema(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.repo = Repository(self.session_factory)
        devices = load_yaml(settings.devices_config)
        flags = dict(devices.get("features") or {})
        flags.update(load_yaml(settings.features_config))
        self.registry = AdapterFactory().build(devices)
        self.features = FeatureService(self.repo, flags, settings)
        self.scheduler = Scheduler(self.repo, self.registry, self.features, self.hub, self.metrics, settings)

    def rebind(self) -> None:
        self.engine = self._make_engine(self.settings.database_url)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.repo = Repository(self.session_factory)
        self.scheduler.repo = self.repo
        self.features.repo = self.repo

    def startup(self) -> None:
        for device in self.registry.all_devices():
            try:
                device.start()
            except AppError as exc:
                log.warning("adapter start skipped %s: %s", getattr(device, "device_id", "?"), exc.message)
        seed(self)
        self.scheduler.recover_inflight()
        try:
            maybe_auto_backup(self)
        except Exception:
            log.exception("auto backup failed")

    @staticmethod
    def _make_engine(url: str):
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        if url.startswith("sqlite:///"):
            raw = url[len("sqlite:///") :]
            if raw and raw != ":memory:" and not raw.startswith("file:"):
                from pathlib import Path

                Path(raw).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(url, connect_args=connect_args)

    def db_ok(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            log.exception("database check failed")
            return False


def create_app(settings: Settings | None = None) -> FastAPI:
    setup_logging()
    settings = settings or Settings()
    runtime = Runtime(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        runtime.startup()
        yield

    app = FastAPI(
        title="移动环境监测机器人上位机 API",
        version="0.1.0",
        description="API Gateway：常规操作、数据获取、设置。客户端与 MES/SCADA/DCS 只经此入口。",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "operations", "description": "任务、报警处理、批准流"},
            {"name": "data", "description": "测量、报警、报告、机器人、地图"},
            {"name": "settings", "description": "点位、限值、用户、开关、备份"},
        ],
    )
    app.state.runtime = runtime
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        token = request_id_var.set(request_id)
        runtime.metrics.requests += 1
        try:
            if request.url.path.startswith("/api/"):
                runtime.limiter.check(_rate_key(request, runtime))
            response = await call_next(request)
            response.headers["X-Request-Id"] = request_id
            return response
        except AppError as exc:
            runtime.metrics.errors += 1
            return JSONResponse(content=exc.to_body(), status_code=exc.status_code, headers={"X-Request-Id": request_id})
        finally:
            request_id_var.reset(token)

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError):
        runtime.metrics.errors += 1
        return JSONResponse(content=exc.to_body(), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_request: Request, exc: RequestValidationError):
        runtime.metrics.errors += 1
        return JSONResponse(
            content={"code": "VALIDATION_ERROR", "message": "参数错误", "retryable": False, "details": {"errors": exc.errors()}},
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_request: Request, exc: Exception):
        runtime.metrics.errors += 1
        log.exception("unhandled error")
        return JSONResponse(content={"code": "INTERNAL_ERROR", "message": "内部错误", "retryable": True}, status_code=500)

    register_routes(app)
    _customize_openapi(app)
    return app


def _rate_key(request: Request, runtime: Runtime) -> str:
    """已登录按用户或 API Token 分桶；无效 Bearer 与匿名请求共用客户端 IP，避免轮换随机令牌绕过限流。"""
    host = request.client.host if request.client else "local"
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("bearer "):
        token = header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token, runtime.settings.secret_key)
            subject = payload.get("sub") or host
            return f"user:{subject}"
        except ValueError:
            digest = hash_token(token)
            if runtime.repo.role_for_api_token(digest):
                return f"api:{digest[:16]}"
    return f"ip:{host}"


def _customize_openapi(app: FastAPI) -> None:
    def custom():
        if app.openapi_schema:
            return app.openapi_schema
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        components = schema.setdefault("components", {})
        components["securitySchemes"] = {"bearerAuth": {"type": "http", "scheme": "bearer"}}
        error = {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
                "retryable": {"type": "boolean"},
            },
            "required": ["code", "message", "retryable"],
        }
        components.setdefault("schemas", {})["ErrorBody"] = error
        error_body = {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorBody"}}}}
        for path, methods in schema.get("paths", {}).items():
            for method, operation in list(methods.items()):
                if method not in {"get", "post", "patch", "put", "delete"} or not isinstance(operation, dict):
                    continue
                responses = operation.setdefault("responses", {})
                if "422" in responses:
                    responses["422"] = {"description": "VALIDATION_ERROR", **error_body}
                if path.startswith("/api/") and path != "/api/v1/auth/login":
                    operation["security"] = [{"bearerAuth": []}]
                    responses.setdefault("401", {"description": "AUTH_REQUIRED", **error_body})
                    responses.setdefault("403", {"description": "FORBIDDEN", **error_body})
                    responses.setdefault("429", {"description": "RATE_LIMITED", **error_body})
        schema["paths"]["/api/v1/ws"] = {
            "get": {
                "tags": ["data"],
                "summary": "WebSocket 实时推送",
                "description": "查询参数 token。连接后客户端发送 {topics:[...]}。服务端先回放缓冲，再持续推送新事件；15 秒无事件则发送 heartbeat。",
                "security": [{"bearerAuth": []}],
                "responses": {"101": {"description": "Switching Protocols"}},
            }
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom


app = create_app()
