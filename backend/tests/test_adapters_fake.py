from __future__ import annotations

import pytest

from app.adapters.fake import AmrFake, ElevatorFake, ParticleFake
from app.core.errors import DomainError
from app.domain.models import Pose, RobotMode


def test_amr_navigate_and_estop_blocks() -> None:
    amr = AmrFake("robot-01", nav_delay_s=0)
    amr.connect()
    h = amr.navigate_to(Pose(x=1, y=2))
    assert h.status == "succeeded"
    assert amr.get_status().pose and amr.get_status().pose.x == 1
    amr.inject(estop=True)
    assert amr.get_status().mode == RobotMode.ESTOP
    with pytest.raises(DomainError) as ei:
        amr.navigate_to(Pose(x=0, y=0))
    assert ei.value.code == "DEVICE_ESTOP"


def test_elevator_call_enter_exit_and_fail() -> None:
    elv = ElevatorFake("elev-01", floors=[1, 2], delay_s=0)
    elv.connect()
    assert elv.call_elevator(2).status == "succeeded"
    assert elv.enter_elevator().status == "succeeded"
    assert elv.exit_elevator().status == "succeeded"
    elv.inject(fail_next="call")
    with pytest.raises(DomainError) as ei:
        elv.call_elevator(1)
    assert ei.value.code == "DEVICE_OFFLINE"


def test_particle_channels() -> None:
    pc = ParticleFake("pc-01")
    pc.connect()
    pc.start_sample()
    ch = pc.read_channels()
    assert len(ch) == 2
    assert ch[0].quality == "good"
    pc.stop_sample()
