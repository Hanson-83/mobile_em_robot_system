"""简易 HMAC Token（MVP）。真实 IdP / LDAP 为后期占位。"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from collections.abc import Iterable
from dataclasses import dataclass

from app.core.errors import DomainError, auth_required, forbidden

# 权限码对齐 DS §4.2
ROLE_PERMS: dict[str, frozenset[str]] = {
    "admin": frozenset(
        {
            "operations.task.read",
            "operations.task.write",
            "operations.alarm.ack",
            "operations.alarm.close",
            "operations.approval.read",
            "operations.approval.write",
            "data.measurement.read",
            "data.measurement.write",
            "data.alarm.read",
            "data.alarm.export",
            "data.report.read",
            "data.report.write",
            "data.robot.read",
            "data.map.read",
            "settings.point.read",
            "settings.point.write",
            "settings.limit.read",
            "settings.limit.write",
            "settings.user.read",
            "settings.user.write",
            "settings.feature.read",
            "settings.feature.write",
        }
    ),
    "operator": frozenset(
        {
            "operations.task.read",
            "operations.task.write",
            "operations.alarm.ack",
            "operations.alarm.close",
            "operations.approval.read",
            "data.measurement.read",
            "data.measurement.write",
            "data.alarm.read",
            "data.alarm.export",
            "data.report.read",
            "data.robot.read",
            "data.map.read",
            "settings.point.read",
            "settings.limit.read",
        }
    ),
    "viewer": frozenset(
        {
            "operations.task.read",
            "data.measurement.read",
            "data.alarm.read",
            "data.report.read",
            "data.robot.read",
            "data.map.read",
            "settings.point.read",
        }
    ),
    "api_client": frozenset(
        {
            "operations.task.read",
            "operations.task.write",
            "data.measurement.read",
            "data.measurement.write",
            "data.alarm.read",
            "data.robot.read",
            "data.map.read",
        }
    ),
}


@dataclass(frozen=True)
class Principal:
    sub: str
    role: str
    perms: frozenset[str]

    def require(self, *codes: str) -> None:
        for code in codes:
            if code not in self.perms:
                raise forbidden(f"缺少权限: {code}")


def _b64e(raw: bytes) -> str:
    return urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return urlsafe_b64decode(text + pad)


def issue_token(secret: str, sub: str, role: str, ttl_min: int) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "exp": int(time.time()) + ttl_min * 60,
    }
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64e(sig)}"


def parse_token(secret: str, token: str) -> Principal:
    try:
        body, sig = token.split(".", 1)
        expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64d(sig)):
            raise auth_required("令牌无效")
        payload = json.loads(_b64d(body))
        if int(payload["exp"]) < int(time.time()):
            raise auth_required("令牌已过期")
        role = str(payload["role"])
        perms = ROLE_PERMS.get(role)
        if perms is None:
            raise auth_required("未知角色")
        return Principal(sub=str(payload["sub"]), role=role, perms=perms)
    except DomainError:
        raise
    except Exception as exc:  # noqa: BLE001 — 统一转为鉴权失败
        raise auth_required("令牌无效") from exc


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, digest: str) -> bool:
    return hmac.compare_digest(hash_password(password), digest)


def any_perm(principal: Principal, codes: Iterable[str]) -> bool:
    return any(code in principal.perms for code in codes)
