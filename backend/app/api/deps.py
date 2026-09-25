from __future__ import annotations

from typing import Annotated

from fastapi import Header, Request

from app.core.errors import auth_required
from app.core.security import Principal, parse_token


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


async def get_principal(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise auth_required()
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise auth_required()
    settings = request.app.state.settings
    principal = parse_token(settings.jwt_secret, token)
    request.app.state.rate_limiter.check(principal.sub)
    request.state.principal = principal
    return principal
