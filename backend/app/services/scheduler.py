"""编排状态机（M2）。技能经适配层执行；电梯只走 ElevatorAdapter。"""

from __future__ import annotations

import logging
from typing import Any

from app.adapters.factory import DeviceRegistry
from app.core.config import FeaturesFile
from app.core.errors import DomainError, device_estop, not_found, validation_error
from app.domain.dto import MeasurementIn, Pose, Quality, SkillStep, TaskInstance, TaskState
from app.services.lock import LockService
from app.services.stores import MemoryStores

log = logging.getLogger("mer.scheduler")

TERMINAL = {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}


class Scheduler:
    def __init__(
        self,
        registry: DeviceRegistry,
        locks: LockService,
        stores: MemoryStores,
        features: FeaturesFile,
    ) -> None:
        self.registry = registry
        self.locks = locks
        self.stores = stores
        self.features = features

    async def start(self, task_id: str) -> TaskInstance:
        task = self.stores.get_task(task_id)
        if task.state not in {TaskState.CREATED, TaskState.QUEUED}:
            raise validation_error(f"任务不可启动: {task.state}")
        task.state = TaskState.QUEUED
        task.state = TaskState.DISPATCHED
        task.state = TaskState.RUNNING
        try:
            for skill in task.skills:
                if task.state == TaskState.CANCELLED:
                    self._release_task_locks(task.id)
                    return task
                await self._run_skill(task, skill)
            task.state = TaskState.SUCCEEDED
            self.stores.add_report(task.id)
        except DomainError as exc:
            task.state = TaskState.FAILED
            task.reason = f"{exc.code}: {exc.message}"
            self._release_task_locks(task.id)
            log.warning("task failed", extra={"task_id": task.id, "robot_id": task.robot_id})
        except Exception as exc:  # noqa: BLE001
            task.state = TaskState.FAILED
            task.reason = str(exc)
            self._release_task_locks(task.id)
        return task

    def _amr(self, robot_id: str | None) -> Any:
        if not robot_id or robot_id not in self.registry.robots:
            raise not_found(f"机器人不存在: {robot_id}")
        return self.registry.robots[robot_id]

    def _elevator(self, elevator_id: str) -> Any:
        if elevator_id not in self.registry.elevators:
            raise not_found(f"电梯不存在: {elevator_id}")
        return self.registry.elevators[elevator_id]

    async def _guard_robot(self, robot_id: str | None) -> None:
        status = await self._amr(robot_id).get_status()
        if status.estop or status.mode.value == "estop":
            raise device_estop(f"AMR {robot_id} 急停")
        if not status.online:
            raise DomainError("DEVICE_OFFLINE", f"AMR {robot_id} 离线", retryable=True, status_code=503)

    async def _run_skill(self, task: TaskInstance, skill: SkillStep) -> None:
        await self._guard_robot(task.robot_id)
        kind = skill.type
        params = skill.params
        if kind == "navigate_to":
            target = params.get("pose") or params.get("point_id") or Pose()
            if isinstance(target, dict):
                target = Pose.model_validate(target)
            await self._amr(task.robot_id).navigate_to(target)
            return
        if kind == "dock_charge":
            await self._amr(task.robot_id).dock_charge()
            return
        if kind in {"call_elevator", "enter_elevator", "exit_elevator"}:
            if not self.features.elevator_skills:
                raise validation_error("电梯技能已关闭")
            elev_id = str(params.get("elevator_id", "elev-01"))
            if kind == "call_elevator":
                self.locks.acquire("elevator", elev_id, holder=task.id)
                floor = int(params.get("floor", 1))
                await self._elevator(elev_id).call_elevator(floor)
            elif kind == "enter_elevator":
                await self._elevator(elev_id).enter_elevator()
            else:
                await self._elevator(elev_id).exit_elevator()
                self.locks.release("elevator", elev_id, holder=task.id)
            return
        if kind == "sample_particle":
            inst_id = str(params.get("instrument_id", "pc-01"))
            inst = self.registry.instruments.get(inst_id)
            if inst is None:
                raise not_found(f"仪表不存在: {inst_id}")
            await inst.start_sample(params)
            readings = await inst.read_channels()
            await inst.stop_sample()
            for reading in readings:
                self.stores.upsert_measurement(
                    MeasurementIn(
                        task_id=task.id,
                        robot_id=task.robot_id,
                        device_id=inst_id,
                        sample_id=f"{task.id}-{reading.channel}",
                        metric=f"particle.{reading.channel}",
                        value=reading.value,
                        unit=reading.unit,
                        quality=Quality.GOOD,
                        point_id=params.get("point_id"),
                    )
                )
            return
        if kind == "read_climate":
            inst_id = str(params.get("instrument_id", "th-01"))
            inst = self.registry.instruments[inst_id]
            reading = await inst.read_temp_humidity()
            self.stores.upsert_measurement(
                MeasurementIn(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    device_id=inst_id,
                    sample_id=f"{task.id}-th",
                    metric="climate.temp",
                    value=reading.temperature_c,
                    unit="C",
                )
            )
            return
        if kind == "read_airflow":
            inst_id = str(params.get("instrument_id", "af-01"))
            inst = self.registry.instruments[inst_id]
            reading = await inst.read_air_speed()
            self.stores.upsert_measurement(
                MeasurementIn(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    device_id=inst_id,
                    sample_id=f"{task.id}-af",
                    metric="airflow.speed",
                    value=reading.speed_mps,
                    unit="m/s",
                )
            )
            return
        raise validation_error(f"未知技能: {kind}")

    def _release_task_locks(self, task_id: str) -> None:
        self.locks.release_holder(task_id)
