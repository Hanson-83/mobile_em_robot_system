"""MVP 鉴权：Bearer Token（开发用 HMAC 签名占位，非生产 JWT）。"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass

from app.core.errors import DomainError

# 开发占位账号；生产须外置用户库。默认口令仅用于 Fake/CI。
DEV_USERS = {
    "admin": {"password": "admin", "roles": ["admin"], "perms": ["*"]},
    "operator": {
        "password": "operator",
        "roles": ["operator"],
        "perms": [
            "operations.task.read",
            "operations.task.write",
            "operations.alarm.ack",
            "operations.alarm.close",
            "data.measurement.read",
            "data.alarm.read",
            "data.robot.read",
            "data.map.read",
            "data.report.read",
        ],
    },
    "api_client": {"password": "api_client", "roles": ["api_client"], "perms": ["*"]},
}


@dataclass
class Principal:
    username: str
    roles: list[str]
    perms: list[str]


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
    expected = hmac.new(secret.encode(), f"{username}:{exp}".encode(), hashlib.sha256).hexdigest()[
        :32
    ]
    if not hmac.compare_digest(expected, sig):
        raise DomainError("AUTH_REQUIRED", "Token 校验失败")
    user = DEV_USERS.get(username)
    if not user:
        raise DomainError("AUTH_REQUIRED", "未知用户")
    return Principal(username=username, roles=list(user["roles"]), perms=list(user["perms"]))


def authenticate(username: str, password: str, secret: str) -> str:
    user = DEV_USERS.get(username)
    if not user or user["password"] != password:
        raise DomainError("AUTH_REQUIRED", "用户名或密码错误")
    return issue_token(username, secret)


def require_perm(principal: Principal, perm: str) -> None:
    if "*" in principal.perms or perm in principal.perms:
        return
    raise DomainError("FORBIDDEN", f"缺少权限 {perm}")
