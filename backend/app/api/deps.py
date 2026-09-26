from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header

from app.core.errors import DomainError
from app.core.integrations import resolve_bearer
from app.core.security import Principal, require_perm
from app.main_state import get_limiter, get_secret


def bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise DomainError("AUTH_REQUIRED", "缺少 Authorization: Bearer")
    return authorization.split(" ", 1)[1].strip()


def current_user(token: Annotated[str, Depends(bearer_token)]) -> Principal:
    principal = resolve_bearer(token, get_secret())
    get_limiter().check(principal.username)
    return principal


def require(perm: str):
    def _dep(user: Annotated[Principal, Depends(current_user)]) -> Principal:
        require_perm(user, perm)
        return user

    return _dep
