from __future__ import annotations

import pytest

from app.core.errors import DomainError
from app.services.mutex import MutexService


def test_mutex_conflict_fail() -> None:
    m = MutexService()
    m.acquire("point", "P1", holder="t1")
    with pytest.raises(DomainError) as ei:
        m.acquire("point", "P1", holder="t2", on_conflict="fail")
    assert ei.value.code == "CONFLICT_MUTEX"
    m.release("point", "P1", holder="t1")
    m.acquire("point", "P1", holder="t2")
