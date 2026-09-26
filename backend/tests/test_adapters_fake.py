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
    elv.call_elevator(2)
    st = elv.get_status()
    assert st.floor == 2
    assert st.door == "open"
    elv.enter_elevator()
    assert elv.get_status().door == "closed"
    elv.exit_elevator()
    assert elv.get_status().door == "open"
    for op in ("call", "enter", "exit"):
        elv.inject(fail_next=op)
        with pytest.raises(DomainError) as ei:
            if op == "call":
                elv.call_elevator(1)
            elif op == "enter":
                elv.enter_elevator()
            else:
                elv.exit_elevator()
        assert ei.value.code == "DEVICE_OFFLINE"


def test_instrument_curves_and_exceed() -> None:
    pc = ParticleFake("pc-01", curve=[10.0, 20.0])
    pc.connect()

    def ch(name: str, readings):
        return next(r for r in readings if r.channel == name)

    assert ch("0.5um", pc.read_channels()).value == 10.0
    assert ch("0.5um", pc.read_channels()).value == 20.0
    pc.inject(exceed=True)
    assert ch("0.5um", pc.read_channels()).quality == "uncertain"
    from app.adapters.fake import AirflowFake, ClimateFake

    th = ClimateFake("th-01", temp_curve=[21.0, 22.5])
    th.connect()
    assert th.read_temp_humidity().temperature_c == 21.0
    th.inject(exceed=True)
    assert th.read_temp_humidity().temperature_c == 40.0
    af = AirflowFake("af-01", speed_curve=[0.3])
    af.connect()
    assert af.read_air_speed().speed_mps == 0.3
    af.inject(exceed=True)
    assert af.read_air_speed().speed_mps == 2.5


def test_particle_channels() -> None:
    pc = ParticleFake("pc-01")
    pc.connect()
    pc.start_sample()
    ch = pc.read_channels()
    names = [r.channel for r in ch]
    assert names == ["0.1um", "0.5um", "1.0um", "5.0um"]
    assert ch[0].quality == "good"
    assert ch[0].unit == "count/cf"
    pc.stop_sample()
