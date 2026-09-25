"""口令哈希与 Bearer Token。不引入额外加密库，避免原生依赖。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(digest.hex(), digest_hex)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_token(
    *,
    subject: str,
    username: str,
    permissions: list[str],
    secret: str,
    ttl_min: int,
    token_kind: str = "session",
) -> str:
    payload = {
        "sub": subject,
        "username": username,
        "perms": permissions,
        "kind": token_kind,
        "exp": int(time.time()) + ttl_min * 60,
    }
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def decode_token(token: str, secret: str) -> dict:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("malformed token") from exc
    expected = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError("bad signature")
    padded = body + "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("expired")
    return payload
