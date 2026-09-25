"""本地账号（MVP）。LDAP/OIDC 后期占位。"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import auth_required
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


def bootstrap_directory(admin_password: str, operator_password: str) -> UserDirectory:
    return UserDirectory(
        [
            LocalUser("admin", "admin", hash_password(admin_password)),
            LocalUser("operator", "operator", hash_password(operator_password)),
            LocalUser("viewer", "viewer", hash_password("viewer")),
        ]
    )
