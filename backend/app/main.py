from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

import app.main_state as state
from app.adapters.factory import AdapterFactory
from app.api.routes import auth, misc, robots, tasks
from app.core.config import load_devices, load_features, resolve_config_dir, validate_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.main_state import settings

OPENAPI_TAGS = [
    {"name": "operations", "description": "常规操作（任务/登录/报警确认/批准）"},
    {"name": "data", "description": "数据获取（测量/报警/报告/机器人/地图）"},
    {"name": "settings", "description": "设置类（点位/限值/用户/开关）"},
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    validate_settings(settings)
    cfg_dir = resolve_config_dir(settings)
    devices = load_devices(cfg_dir)
    feats = load_features(cfg_dir)
    state.features = feats
    # 将 features 段从 devices yaml 合并（example 把 features 放在同一文件）
    if devices.features:
        merged = feats.model_dump()
        merged.update({k: v for k, v in devices.features.items() if k in merged})
        from app.core.config import FeaturesConfig

        state.features = FeaturesConfig.model_validate(merged)
    state.registry = AdapterFactory.build(devices)
    assert state.registry is not None
    state.registry.start_all()
    yield
    if state.registry:
        state.registry.stop_all()


app = FastAPI(
    title="MER API Gateway",
    version="0.1.0",
    description="移动环境监测机器人上位机 API Gateway（M1 草图）",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(auth.router)
app.include_router(robots.router)
app.include_router(tasks.router)
app.include_router(misc.router)


@app.get("/health", tags=["data"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["data"])
def ready() -> dict[str, object]:
    reg = state.registry
    items = reg.health() if reg else []
    return {"status": "ready", "adapters": items, "e_sign": state.features.e_sign}


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
    schema["info"]["x-mer-groups"] = ["operations", "data", "settings"]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi  # type: ignore[method-assign]
