from __future__ import annotations

import pytest

from app.adapters.elevator.fake import ElevatorFake
from app.adapters.factory import AdapterFactory
from app.core.config import load_devices
from app.core.errors import DomainError
from app.services.lock import LockService


@pytest.mark.asyncio
async def test_elevator_fake_call_enter_exit():
    elv = ElevatorFake("elev-01", floors=[1, 2, 3], delay_s=0)
    await elv.connect()
    called = await elv.call_elevator(2)
    assert called.status == "succeeded"
    status = await elv.get_status()
    assert status.floor == 2
    assert status.door == "open"
    entered = await elv.enter_elevator()
    assert entered.status == "succeeded"
    assert (await elv.get_status()).door == "closed"
    exited = await elv.exit_elevator()
    assert exited.status == "succeeded"


@pytest.mark.asyncio
async def test_elevator_fake_inject_fail():
    elv = ElevatorFake("elev-01", delay_s=0)
    await elv.connect()
    elv.inject(fail_next="call")
    with pytest.raises(DomainError) as exc:
        await elv.call_elevator(1)
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_elevator_lock_then_skill(settings):
    devices = load_devices(settings.repo_root / "config/devices.example.yaml")
    registry = AdapterFactory.build(devices)
    elv = registry.elevators["elev-01"]
    await elv.connect()
    locks = LockService()
    locks.acquire("elevator", "elev-01", holder="task-A")
    with pytest.raises(DomainError) as exc:
        locks.acquire("elevator", "elev-01", holder="task-B")
    assert exc.value.code == "CONFLICT_MUTEX"
    await elv.call_elevator(3)
    locks.release("elevator", "elev-01", holder="task-A")
    locks.acquire("elevator", "elev-01", holder="task-B")
    assert locks.holder_of("elevator", "elev-01") == "task-B"
