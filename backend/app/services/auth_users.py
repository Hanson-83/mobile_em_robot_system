"""本地账号（MVP）。LDAP/OIDC 后期占位。"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import auth_required, validation_error
from app.core.security import hash_password, verify_password


@dataclass
class LocalUser:
    username: str
    role: str
    password_hash: str


class UserDirectory:
    def __init__(self, users: list[LocalUser]) -> None:
        self._users = {u.username: u for u in users}

    def authenticate(self, username: str, password: str) -> LocalUser:
        user = self._users.get(username)
        if not user or not verify_password(password, user.password_hash):
            raise auth_required("用户名或密码错误")
        return user

    def list_public(self) -> list[dict[str, str]]:
        return [{"username": u.username, "role": u.role} for u in self._users.values()]

    def create(self, username: str, role: str, password: str, *, min_len: int = 8) -> dict[str, str]:
        if username in self._users:
            raise validation_error(f"用户已存在: {username}")
        if role not in {"admin", "operator", "viewer", "api_client"}:
            raise validation_error(f"未知角色: {role}")
        if len(password) < min_len:
            raise validation_error(f"密码长度不足 {min_len}")
        self._users[username] = LocalUser(username, role, hash_password(password))
        return {"username": username, "role": role}


def bootstrap_directory(
    admin_password: str,
    operator_password: str,
    viewer_password: str,
) -> UserDirectory:
    return UserDirectory(
        [
            LocalUser("admin", "admin", hash_password(admin_password)),
            LocalUser("operator", "operator", hash_password(operator_password)),
            LocalUser("viewer", "viewer", hash_password(viewer_password)),
        ]
    )
