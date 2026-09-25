"""API Gateway 应用入口。对外唯一入口；对内不暴露适配器。"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.factory import AdapterFactory
from app.api.routes import data, ops, settings_api
from app.core.config import Settings, assert_runtime_secrets, load_devices, load_features, resolve_path
from app.core.errors import DomainError
from app.core.logging import setup_logging
from app.core.rate_limit import TokenRateLimiter
from app.services.auth_users import bootstrap_directory
from app.services.lock import LockService
from app.services.scheduler import Scheduler
from app.services.stores import MemoryStores

OPENAPI_TAGS = [
    {"name": "operations", "description": "常规操作：登录、任务、报警确认、批准流"},
    {"name": "data", "description": "数据获取：测量、机器人、地图、报告、报警查询/导出"},
    {"name": "settings", "description": "设置类：点位、限值、用户、系统开关"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = app.state.registry
    for adapter in registry.all_adapters():
        await adapter.start()
    try:
        yield
    finally:
        for adapter in registry.all_adapters():
            await adapter.stop()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    assert_runtime_secrets(settings)
    setup_logging(settings.log_level)
    devices_path = resolve_path(settings, settings.devices_path)
    features_path = resolve_path(settings, settings.features_path)
    devices = load_devices(devices_path)
    features = load_features(features_path)
    registry = AdapterFactory.build(devices)

    app = FastAPI(
        title="MER Host API Gateway",
        version="0.1.0",
        description=(
            "移动环境监测机器人上位机对外统一入口。"
            "分组：operations / data / settings。"
            "破坏性变更走 /api/v2。"
        ),
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.devices = devices
    app.state.features = features
    app.state.registry = registry
    app.state.stores = MemoryStores()
    app.state.locks = LockService(features.resource_mutex_config)
    app.state.scheduler = Scheduler(registry, app.state.locks, app.state.stores, features)
    app.state.users = bootstrap_directory(
        settings.bootstrap_admin_password,
        settings.bootstrap_operator_password,
        settings.bootstrap_viewer_password,
    )
    app.state.rate_limiter = TokenRateLimiter(features.gateway.rate_limit_per_min)
    app.state.repo_root = Path(settings.repo_root)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_body())

    @app.get("/health", tags=["operations"])
    def health() -> dict:
        return {"status": "ok", "service": "mer-gateway"}

    @app.get("/ready", tags=["operations"])
    async def ready() -> dict:
        adapters = {}
        for adapter in registry.all_adapters():
            info = await adapter.health()
            key = str(info.get("id") or getattr(adapter, "robot_id", None) or id(adapter))
            adapters[key] = "up" if info.get("ok") else "down"
        status = "ok" if adapters and all(v == "up" for v in adapters.values()) else "not_ready"
        return {"status": status, "adapters": adapters}

    app.include_router(ops)
    app.include_router(data)
    app.include_router(settings_api)
    return app


app = create_app()
