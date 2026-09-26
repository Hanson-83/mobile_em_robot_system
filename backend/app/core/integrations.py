"""服务账号 API Token（长生命周期）。仅环境注入，禁止入库。"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

from app.core.errors import DomainError
from app.core.security import Principal, authenticate, parse_token



# MES 首批对接所需权限（用户 2026-09-26 确认）
MES_PERMS = [
    "operations.task.read",
    "operations.task.write",
    "data.measurement.read",
    "data.alarm.read",
    "data.robot.read",
    "data.map.read",
]


def _api_tokens() -> dict[str, dict[str, Any]]:
    """MER_API_TOKENS_JSON: { "token_value": {"client_id": "...", "roles": [...], "perms": [...]} }"""
    raw = os.environ.get("MER_API_TOKENS_JSON", "").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise DomainError("INTERNAL_ERROR", "MER_API_TOKENS_JSON 格式错误")
    return data


def resolve_bearer(token: str, secret: str) -> Principal:
    tokens = _api_tokens()
    if token in tokens:
        meta = tokens[token]
        client_id = str(meta.get("client_id") or "api_client")
        roles = list(meta.get("roles") or ["api_client"])
        perms = list(meta.get("perms") or MES_PERMS)
        return Principal(username=client_id, roles=roles, perms=perms)
    return parse_token(token, secret)


def issue_session(username: str, password: str, secret: str, ttl_sec: int = 86400) -> str:
    return authenticate(username, password, secret)


def describe_mes_catalog() -> dict[str, Any]:
    return {
        "integration": "mes_scada_dcs",
        "version": "1.0.0",
        "scope": [
            "task.create",
            "task.start",
            "task.stop",
            "task.status",
            "realtime.read",
        ],
        "paths": [
            "POST /api/v1/integrations/mes/tasks",
            "GET /api/v1/integrations/mes/tasks",
            "GET /api/v1/integrations/mes/tasks/{id}",
            "POST /api/v1/integrations/mes/tasks/{id}/start",
            "POST /api/v1/integrations/mes/tasks/{id}/stop",
            "GET /api/v1/integrations/mes/realtime",
        ],
        "auth": "Authorization: Bearer <session_token|api_token>",
        "desktop_mobile": "deferred",
        "breaking_change_policy": "破坏性变更走 /api/v2；本版兼容变更保留 v1",
    }


def hash_token_hint(token: str) -> str:
    return hmac.new(b"mer-token-hint", token.encode(), hashlib.sha256).hexdigest()[:8]
