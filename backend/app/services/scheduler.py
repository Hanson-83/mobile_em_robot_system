"""调度编排：状态机 + 资源锁（电梯先于点位）+ 断线重连 + 采样/报警。"""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.config import DevicesConfig, FeaturesConfig
from app.core.errors import DomainError
from app.domain.task_fsm import TERMINAL, assert_transition
from app.services.limits import load_limits, particle_exceeds, scalar_exceeds
from app.services.mutex import MutexService
from app.services.store import Store


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Scheduler:
    def __init__(
        self,
        *,
        registry: Any,
        devices: DevicesConfig,
        features: FeaturesConfig,
        mutex: MutexService,
        store: Store,
        limits: dict[str, Any],
    ) -> None:
        self.registry = registry
        self.devices = devices
        self.features = features
        self.mutex = mutex
        self.store = store
        self.limits = limits

    def recover_interrupted(self) -> None:
        """进程重启：Running/Dispatched 记为失败，Queued 保留待再次 tick。"""
        for task in self.store.list_tasks_in({"Running", "Dispatched"}):
            self._transition(task, "Failed")
            task["error"] = {
                "code": "PROCESS_LOST",
                "message": "进程中断，任务未完成",
                "retryable": True,
            }
            self.store.save_task(task)

    def submit(self, body: dict[str, Any], *, auto_start: bool = True) -> dict[str, Any]:
        robot_id = body["robot_id"]
        if robot_id not in self.registry.robots:
            raise DomainError("NOT_FOUND", f"机器人 {robot_id} 不存在")
        if body.get("elevator_id") and body["elevator_id"] not in self.registry.elevators:
            raise DomainError("NOT_FOUND", f"电梯 {body['elevator_id']} 不存在")
        task = {
            "id": uuid4().hex[:12],
            "state": "Created",
            "robot_id": robot_id,
            "point_id": body.get("point_id"),
            "skills": body.get("skills") or ["navigate", "sample"],
            "elevator_id": body.get("elevator_id"),
            "elevator_floor": body.get("elevator_floor"),
            "samples": [],
            "elevator_trace": [],
            "alarms": [],
            "reconnects": 0,
            "error": None,
            "queue_reason": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.save_task(task)
        self._transition(task, "Queued")
        self.store.save_task(task)
        if auto_start:
            self.pump()
        got = self.store.get_task(task["id"])
        assert got is not None
        return got

    def start(self, task_id: str) -> dict[str, Any]:
        task = self._require(task_id)
        if task["state"] in TERMINAL:
            raise DomainError("VALIDATION_ERROR", f"任务已终态 {task['state']}")
        self.pump()
        got = self.store.get_task(task_id)
        assert got is not None
        return got

    def stop(self, task_id: str) -> dict[str, Any]:
        task = self._require(task_id)
        if task["state"] in TERMINAL:
            raise DomainError("VALIDATION_ERROR", f"任务已终态 {task['state']}")
        if task["state"] == "Queued":
            self._transition(task, "Cancelled")
            task["queue_reason"] = None
            self.store.save_task(task)
            return task
        robot = self.registry.robots.get(task["robot_id"])
        if robot:
            robot.cancel(None)
        self._transition(task, "Cancelled")
        self._release(task)
        self.store.save_task(task)
        return task

    def pump(self) -> None:
        for _ in range(64):
            progressed = False
            for task in self.store.list_tasks_in({"Queued"}):
                if self._try_run(task):
                    progressed = True
            if not progressed:
                return

    def _try_run(self, task: dict[str, Any]) -> bool:
        """跑到终态返回 True；仍在排队返回 False。"""
        held: list[tuple[str, str]] = []
        policy = self.features.on_conflict
        try:
            if task.get("elevator_id"):
                if not self._lock("elevator", task["elevator_id"], task["id"], policy):
                    task["queue_reason"] = "elevator"
                    self.store.save_task(task)
                    return False
                held.append(("elevator", task["elevator_id"]))
            if task.get("point_id"):
                if not self._lock("point", task["point_id"], task["id"], policy):
                    self._release_held(held, task["id"])
                    task["queue_reason"] = "point"
                    self.store.save_task(task)
                    return False
                held.append(("point", task["point_id"]))
            self._transition(task, "Dispatched")
            self._transition(task, "Running")
            self.store.save_task(task)
            self._execute(task)
            self._transition(task, "Succeeded")
            task["queue_reason"] = None
        except DomainError as exc:
            if task["state"] == "Queued":
                self._release_held(held, task["id"])
                self.store.save_task(task)
                raise
            if task["state"] == "Dispatched":
                self._transition(task, "Failed")
            elif task["state"] == "Running":
                self._transition(task, "Failed")
            task["error"] = {"code": exc.code, "message": exc.message, "retryable": exc.retryable}
            task["queue_reason"] = None
        finally:
            if task["state"] in TERMINAL:
                self._release_held(held, task["id"])
        self.store.save_task(task)
        return task["state"] in TERMINAL

    def _lock(self, rtype: str, rid: str, holder: str, policy: str) -> bool:
        got = self.mutex.try_acquire(rtype, rid, holder, on_conflict=policy)
        return got is not None

    def _execute(self, task: dict[str, Any]) -> None:
        robot = self.registry.robots[task["robot_id"]]
        self._call(task, robot, lambda: robot.navigate_to(task.get("point_id") or "P0"))
        if task.get("elevator_id") and self.features.elevator_skills:
            elv = self.registry.elevators[task["elevator_id"]]
            floor = task["elevator_floor"] if task["elevator_floor"] is not None else 2

            def _call_elv() -> None:
                task["elevator_trace"].append(elv.call_elevator(floor).status)

            def _enter() -> None:
                task["elevator_trace"].append(elv.enter_elevator().status)

            def _exit() -> None:
                task["elevator_trace"].append(elv.exit_elevator().status)

            self._call(task, elv, _call_elv)
            self._call(task, elv, _enter)
            self._call(task, elv, _exit)
        self._sample(task)

    def _sample(self, task: dict[str, Any]) -> None:
        allowed = {
            i.id
            for i in self.devices.instruments
            if not i.robot_id or i.robot_id == task["robot_id"]
        }
        for iid, inst in self.registry.instruments.items():
            if iid not in allowed:
                continue
            if hasattr(inst, "start_sample"):
                self._call(task, inst, lambda inst=inst: inst.start_sample())
                readings = self._call(task, inst, lambda inst=inst: inst.read_channels())
                task["samples"].append(
                    {"instrument_id": iid, "readings": [asdict(r) for r in readings]}
                )
                self._persist_particle(task, iid, readings)
                self._call(task, inst, lambda inst=inst: inst.stop_sample())
            elif hasattr(inst, "read_temp_humidity"):
                reading = self._call(task, inst, lambda inst=inst: inst.read_temp_humidity())
                task["samples"].append({"instrument_id": iid, "readings": asdict(reading)})
                self._persist_scalar(
                    task,
                    iid,
                    "temperature_c",
                    reading.temperature_c,
                    "C",
                    scalar_exceeds("temperature_c", reading.temperature_c, self.limits),
                )
                self._persist_scalar(
                    task,
                    iid,
                    "humidity_pct",
                    reading.humidity_pct,
                    "%",
                    scalar_exceeds("humidity_pct", reading.humidity_pct, self.limits),
                )
            elif hasattr(inst, "read_air_speed"):
                reading = self._call(task, inst, lambda inst=inst: inst.read_air_speed())
                task["samples"].append({"instrument_id": iid, "readings": asdict(reading)})
                self._persist_scalar(
                    task,
                    iid,
                    "speed_mps",
                    reading.speed_mps,
                    "m/s",
                    scalar_exceeds("speed_mps", reading.speed_mps, self.limits),
                )

    def _persist_particle(self, task: dict[str, Any], instrument_id: str, readings: list[Any]) -> None:
        for r in readings:
            exceeded = particle_exceeds(r.channel, r.value, self.limits)
            self._put_measurement(task, instrument_id, r.channel, r.value, r.unit, exceeded)

    def _persist_scalar(
        self,
        task: dict[str, Any],
        instrument_id: str,
        metric: str,
        value: float,
        unit: str,
        exceeded: bool,
    ) -> None:
        self._put_measurement(task, instrument_id, metric, value, unit, exceeded)

    def _put_measurement(
        self,
        task: dict[str, Any],
        instrument_id: str,
        metric: str,
        value: float,
        unit: str,
        exceeded: bool,
    ) -> None:
        key = hashlib.sha1(f"{task['id']}|{instrument_id}|{metric}".encode()).hexdigest()
        body = {
            "task_id": task["id"],
            "instrument_id": instrument_id,
            "metric": metric,
            "value": value,
            "unit": unit,
            "quality": "uncertain" if exceeded else "good",
            "idempotency_key": key,
        }
        self.store.put_measurement(key, body)
        if exceeded:
            alarm_id = uuid4().hex[:12]
            alarm = {
                "id": alarm_id,
                "state": "active",
                "severity": "high",
                "task_id": task["id"],
                "message": f"{instrument_id} {metric}={value}{unit} 超限",
                "metric": metric,
            }
            self.store.add_alarm(alarm)
            task["alarms"].append(alarm_id)

    def _call(self, task: dict[str, Any], device: Any, fn: Any) -> Any:
        attempts = max(1, int(self.features.reconnect_attempts))
        reconnect = self.features.session_on_disconnect == "reconnect"
        last: DomainError | None = None
        for i in range(attempts):
            try:
                health = device.health() if hasattr(device, "health") else {"online": True}
                if not health.get("online"):
                    task["reconnects"] = int(task.get("reconnects") or 0) + 1
                    device.connect()
                return fn()
            except DomainError as exc:
                last = exc
                if exc.code != "DEVICE_OFFLINE" or not reconnect or i == attempts - 1:
                    raise
                task["reconnects"] = int(task.get("reconnects") or 0) + 1
                try:
                    device.connect()
                except DomainError as conn_exc:
                    last = conn_exc
        assert last is not None
        raise last

    def _transition(self, task: dict[str, Any], dst: str) -> None:
        assert_transition(task["state"], dst)
        task["state"] = dst
        task["updated_at"] = _now()

    def _release(self, task: dict[str, Any]) -> None:
        if task.get("elevator_id"):
            self.mutex.release("elevator", task["elevator_id"], task["id"])
        if task.get("point_id"):
            self.mutex.release("point", task["point_id"], task["id"])

    def _release_held(self, held: list[tuple[str, str]], holder: str) -> None:
        for rtype, rid in held:
            self.mutex.release(rtype, rid, holder)
        held.clear()

    def _require(self, task_id: str) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if not task:
            raise DomainError("NOT_FOUND", f"任务 {task_id} 不存在")
        return task


def build_scheduler(
    *,
    registry: Any,
    devices: DevicesConfig,
    features: FeaturesConfig,
    mutex: MutexService,
    store: Store,
    config_dir: Any,
) -> Scheduler:
    return Scheduler(
        registry=registry,
        devices=devices,
        features=features,
        mutex=mutex,
        store=store,
        limits=load_limits(config_dir),
    )
