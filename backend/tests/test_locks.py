from __future__ import annotations

import pytest

from app.core.config import MutexFeatures
from app.core.errors import DomainError
from app.services.lock import RESOURCE_ORDER, LockService


def test_lock_order_documented():
    assert RESOURCE_ORDER == ("zone", "elevator", "charger", "point")


def test_fail_conflict_policy():
    svc = LockService(MutexFeatures(on_conflict="fail"))
    svc.acquire("point", "P1", "A")
    with pytest.raises(DomainError) as exc:
        svc.acquire("point", "P1", "B")
    assert exc.value.code == "CONFLICT_MUTEX"
    svc.release("point", "P1", "A")
    svc.acquire("point", "P1", "B")
    assert svc.holder_of("point", "P1") == "B"
