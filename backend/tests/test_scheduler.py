from __future__ import annotations

import pytest

from app.domain.dto import SkillStep, TaskCreate, TaskState


@pytest.mark.asyncio
async def test_fake_task_with_elevator_and_sample(app):
    for adapter in app.state.registry.all_adapters():
        await adapter.start()
    stores = app.state.stores
    scheduler = app.state.scheduler
    task = stores.create_task(
        TaskCreate(
            name="跨层巡检",
            robot_id="robot-01",
            skills=[
                SkillStep(type="call_elevator", params={"elevator_id": "elev-01", "floor": 2}),
                SkillStep(type="enter_elevator", params={"elevator_id": "elev-01"}),
                SkillStep(type="exit_elevator", params={"elevator_id": "elev-01"}),
                SkillStep(type="navigate_to", params={"point_id": "P1"}),
                SkillStep(type="sample_particle", params={"instrument_id": "pc-01", "point_id": "P1"}),
                SkillStep(type="read_climate", params={"instrument_id": "th-01"}),
                SkillStep(type="read_airflow", params={"instrument_id": "af-01"}),
            ],
        )
    )
    done = await scheduler.start(task.id)
    assert done.state == TaskState.SUCCEEDED
    assert any(m.metric.startswith("particle.") for m in stores.measurements.values())
    assert any(r.task_ref == task.id for r in stores.reports.values())
    assert stores.approvals == {} or app.state.features.e_sign is False
    elev = app.state.registry.elevators["elev-01"]
    status = await elev.get_status()
    assert status.floor == 2
    assert app.state.locks.holder_of("elevator", "elev-01") is None


@pytest.mark.asyncio
async def test_estop_fails_task(app):
    for adapter in app.state.registry.all_adapters():
        await adapter.start()
    amr = app.state.registry.robots["robot-01"]
    amr.inject(estop=True)
    task = app.state.stores.create_task(
        TaskCreate(
            name="急停",
            robot_id="robot-01",
            skills=[SkillStep(type="navigate_to", params={"point_id": "P1"})],
        )
    )
    done = await app.state.scheduler.start(task.id)
    assert done.state == TaskState.FAILED
    assert done.reason and "ESTOP" in done.reason
    amr.inject(estop=False)


def test_start_via_gateway(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "name": "gw-elev",
            "robot_id": "robot-01",
            "skills": [
                {"type": "call_elevator", "params": {"elevator_id": "elev-01", "floor": 1}},
                {"type": "enter_elevator", "params": {"elevator_id": "elev-01"}},
                {"type": "exit_elevator", "params": {"elevator_id": "elev-01"}},
            ],
        },
    )
    task_id = created.json()["id"]
    started = client.post(f"/api/v1/tasks/{task_id}/start", headers=headers)
    assert started.status_code == 200
    assert started.json()["state"] == "Succeeded"
