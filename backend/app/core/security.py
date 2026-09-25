"""MVP 鉴权：Bearer HMAC Token。账号仅经环境注入，禁止源码内置口令。"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from app.core.errors import DomainError


@dataclass
class Principal:
    username: str
    roles: list[str]
    perms: list[str]


def _dev_users() -> dict[str, Any]:
    from app.main_state import settings

    if not settings.mer_allow_dev_auth:
        return {}
    raw = os.environ.get("MER_DEV_USERS_JSON", "").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise DomainError("INTERNAL_ERROR", "MER_DEV_USERS_JSON 格式错误")
    return data


def issue_token(username: str, secret: str, ttl_sec: int = 86400) -> str:
    exp = int(time.time()) + ttl_sec
    msg = f"{username}:{exp}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()[:32]
    return f"{username}.{exp}.{sig}"


def parse_token(token: str, secret: str) -> Principal:
    parts = token.split(".")
    if len(parts) != 3:
        raise DomainError("AUTH_REQUIRED", "无效 Token")
    username, exp_s, sig = parts
    try:
        exp = int(exp_s)
    except ValueError as exc:
        raise DomainError("AUTH_REQUIRED", "无效 Token") from exc
    if exp < int(time.time()):
        raise DomainError("AUTH_REQUIRED", "Token 已过期")
    expected = hmac.new(secret.encode(), f"{username}:{exp}".encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(expected, sig):
        raise DomainError("AUTH_REQUIRED", "Token 校验失败")
    user = _dev_users().get(username)
    if not user:
        raise DomainError("AUTH_REQUIRED", "未知用户或未启用开发用户库")
    return Principal(username=username, roles=list(user["roles"]), perms=list(user["perms"]))


def authenticate(username: str, password: str, secret: str) -> str:
    users = _dev_users()
    if not users:
        raise DomainError("AUTH_REQUIRED", "用户库未配置（需 MER_ALLOW_DEV_AUTH 与 MER_DEV_USERS_JSON）")
    user = users.get(username)
    if not user or user.get("password") != password:
        raise DomainError("AUTH_REQUIRED", "用户名或密码错误")
    return issue_token(username, secret)


def require_perm(principal: Principal, perm: str) -> None:
    if "*" in principal.perms or perm in principal.perms:
        return
    raise DomainError("FORBIDDEN", f"缺少权限 {perm}")
