"""任务状态迁移（DS §6.1）。终态不可再迁移。"""

from __future__ import annotations

from app.core.errors import DomainError

TRANSITIONS: dict[str, set[str]] = {
    "Created": {"Queued", "Cancelled"},
    "Queued": {"Dispatched", "Failed", "Cancelled"},
    "Dispatched": {"Running", "Failed", "Cancelled"},
    "Running": {"Succeeded", "Failed", "Cancelled"},
    "Succeeded": set(),
    "Failed": set(),
    "Cancelled": set(),
}

TERMINAL = frozenset({"Succeeded", "Failed", "Cancelled"})


def assert_transition(src: str, dst: str) -> None:
    allowed = TRANSITIONS.get(src)
    if allowed is None or dst not in allowed:
        raise DomainError("VALIDATION_ERROR", f"非法任务状态迁移 {src} → {dst}")
