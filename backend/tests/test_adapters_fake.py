from __future__ import annotations

import pytest

from app.adapters.airflow.fake import AirflowFake
from app.adapters.amr.fake import AmrFake
from app.adapters.climate.fake import ClimateFake
from app.adapters.particle.fake import ParticleFake
from app.core.errors import DomainError
from app.domain.dto import Pose, RobotMode


@pytest.mark.asyncio
async def test_amr_fake_navigate_and_status():
    amr = AmrFake("robot-01", delay_s=0)
    await amr.connect()
    handle = await amr.navigate_to(Pose(x=3, y=4, map_id="map-01"))
    assert handle.status == "succeeded"
    status = await amr.get_status()
    assert status.pose is not None
    assert status.pose.x == 3
    assert status.mode == RobotMode.IDLE
    assert "call_elevator" not in dir(amr) or not callable(getattr(amr, "call_elevator", None))
    # 明确：AmrFake 无电梯方法
    assert not hasattr(AmrFake, "call_elevator")
    assert not hasattr(AmrFake, "enter_elevator")
    assert not hasattr(AmrFake, "exit_elevator")


@pytest.mark.asyncio
async def test_amr_fake_estop_blocks_navigate():
    amr = AmrFake("robot-01", delay_s=0)
    await amr.connect()
    amr.inject(estop=True)
    status = await amr.get_status()
    assert status.estop is True
    assert status.mode == RobotMode.ESTOP
    with pytest.raises(DomainError) as exc:
        await amr.navigate_to(Pose(x=1, y=1))
    assert exc.value.code == "DEVICE_ESTOP"


@pytest.mark.asyncio
async def test_instrument_fakes_read():
    pc = ParticleFake("pc-01")
    th = ClimateFake("th-01")
    af = AirflowFake("af-01")
    await pc.connect()
    await th.connect()
    await af.connect()
    await pc.start_sample()
    channels = await pc.read_channels()
    assert len(channels) == 2
    climate = await th.read_temp_humidity()
    assert climate.temperature_c == 22.5
    speed = await af.read_air_speed()
    assert speed.speed_mps == 0.45
