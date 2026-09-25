from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import authenticate
from app.main_state import get_secret

router = APIRouter(prefix="/api/v1/auth", tags=["operations"])


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn) -> LoginOut:
    token = authenticate(body.username, body.password, get_secret())
    return LoginOut(access_token=token)
