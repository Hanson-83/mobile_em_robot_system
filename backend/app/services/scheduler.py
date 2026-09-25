"""任务编排：状态机、简单互斥、电梯技能、采样与报警。"""

from __future__ import annotations

import json
import time
import uuid
from datetime import UTC, datetime, timedelta

from app.adapters.repository import Repository, pose_from_dict, utcnow
from app.core.errors import AppError, conflict_mutex, device_offline, validation_error
from app.core.logging import get_logger, robot_id_var, task_id_var
from app.services.support import (
    FeatureService,
    Metrics,
    RealtimeHub,
    idempotency_key,
    read_with_retry,
)

log = get_logger("mer.scheduler")

LOCK_ORDER = {"zone": 0, "elevator": 1, "charger": 2, "point": 3}
TERMINAL = {"Succeeded", "Failed", "Cancelled"}


class Scheduler:
    def __init__(self, repo: Repository, registry, features: FeatureService, hub: RealtimeHub, metrics: Metrics, settings) -> None:
        self.repo = repo
        self.registry = registry
        self.features = features
        self.hub = hub
        self.metrics = metrics
        self.settings = settings
        self._online_prev: dict[str, bool] = {}

    def default_skills(self, point_id: str) -> list[dict]:
        return [
            {"type": "navigate_to", "params": {"point_id": point_id}},
            {"type": "sample_particle", "params": {"point_id": point_id}},
            {"type": "read_climate", "params": {"point_id": point_id}},
            {"type": "read_airflow", "params": {"point_id": point_id}},
        ]

    def create_task(
        self,
        *,
        robot_id: str,
        skills: list[dict] | None,
        point_id: str | None,
        on_fail: str = "none",
        client_request_id: str | None = None,
        composite_id: str | None = None,
        cluster_id: str | None = None,
        depends_on: str | None = None,
    ) -> tuple[dict, bool]:
        if client_request_id:
            existing = self.repo.get_task_by_client_request(client_request_id)
            if existing:
                return existing, True
        if robot_id not in self.registry.amrs:
            raise validation_error(f"未知机器人 {robot_id}")
        if not skills:
            if not point_id:
                raise validation_error("需要 point_id 或 skills")
            skills = self.default_skills(point_id)
        self._validate_skills(skills)
        # MVP 省略 DS §6.1 的 Created / Dispatched，创建即 Queued，拿到锁即 Running。见待确认 C-17。
        task = self.repo.add_task(
            id=uuid.uuid4().hex,
            robot_id=robot_id,
            status="Queued",
            skills_json=json.dumps(skills, ensure_ascii=False),
            skill_index=0,
            on_fail=on_fail,
            error_code=None,
            error_message=None,
            client_request_id=client_request_id,
            composite_id=composite_id,
            cluster_id=cluster_id,
            depends_on=depends_on,
            timeline_json="[]",
        )
        self.hub.publish("task", {"id": task["id"], "status": task["status"], "robot_id": robot_id})
        return task, False

    def _validate_skills(self, skills: list[dict]) -> None:
        allowed = {
            "navigate_to",
            "dock_charge",
            "sample_particle",
            "read_climate",
            "read_airflow",
            "call_elevator",
            "enter_elevator",
            "exit_elevator",
            "elevator_transfer",
            "wait",
        }
        for skill in skills:
            if skill.get("type") not in allowed:
                raise validation_error(f"未知技能 {skill.get('type')}")

    def recover_inflight(self) -> int:
        count = 0
        for task in self.repo.list_tasks():
            if task["status"] in {"Running", "Dispatched"}:
                task["status"] = "Failed"
                task["error_code"] = "PROCESS_RESTART"
                task["error_message"] = "进程重启，在途任务标记为失败"
                self._append(task, "进程重启，任务失败")
                self.repo.save_task(task)
                self.repo.delete_locks_for_holder(task["id"])
                count += 1
        return count

    def cancel(self, task_id: str) -> dict:
        task = self.repo.get_task(task_id)
        if task["status"] in TERMINAL:
            return task
        if task["status"] == "Running":
            amr = self.registry.amr(task["robot_id"])
            amr.cancel(None)
        task["status"] = "Cancelled"
        task["error_code"] = None
        task["error_message"] = "已取消"
        self._append(task, "取消并释放资源锁")
        self.repo.save_task(task)
        self.repo.delete_locks_for_holder(task["id"])
        self.hub.publish("task", {"id": task["id"], "status": "Cancelled"})
        self._refresh_parents()
        return self.repo.get_task(task_id)

    def drain(self, max_rounds: int = 500) -> None:
        self.poll_devices()
        for _ in range(max_rounds):
            self.repo.expire_locks()
            dispatched = self.dispatch_available()
            stepped = self.step_running()
            if not dispatched and not stepped:
                break
        self.metrics.task_depth = len(self.repo.list_tasks(status="Queued")) + len(self.repo.list_tasks(status="Running"))
        self._refresh_parents()

    def dispatch_available(self) -> int:
        count = 0
        for task in self.repo.list_tasks(status="Queued"):
            if self._dispatch_one(task):
                count += 1
        return count

    def step_running(self) -> int:
        count = 0
        for task in self.repo.list_tasks(status="Running"):
            self._step(task)
            count += 1
        return count

    def poll_devices(self) -> None:
        features = self.features.snapshot()
        for robot_id, amr in self.registry.amrs.items():
            status = amr.get_status()
            previous = self._online_prev.get(robot_id, True)
            self._online_prev[robot_id] = status.online
            if previous and not status.online:
                alarm = self.repo.add_alarm(
                    rule_id="device.offline",
                    severity="critical",
                    state="open",
                    source=robot_id,
                    message=f"机器人 {robot_id} 会话离线",
                    object_ref=robot_id,
                    ack_by=None,
                    note="",
                )
                self.hub.publish("alarm", alarm)
                if features.get("fail_on_disconnect", True):
                    for task in self.repo.list_tasks(status="Running"):
                        if task["robot_id"] == robot_id:
                            self._fail(task, "DEVICE_OFFLINE", "设备离线，任务失败")
            if status.estop or status.mode in {"estop", "fault"}:
                for task in self.repo.list_tasks(status="Running"):
                    if task["robot_id"] == robot_id and task["status"] == "Running":
                        code = "ESTOP" if status.estop or status.mode == "estop" else "FAULT"
                        self._fail(task, code, status.fault_msg or "急停或故障，任务中断")

    def _dispatch_one(self, task: dict) -> bool:
        if task.get("depends_on"):
            parent = self.repo.get_task(task["depends_on"])
            if parent["status"] not in TERMINAL:
                return False
            if parent["status"] != "Succeeded":
                self._fail(task, "DEPENDENCY", "前置任务未成功")
                return False
        self._maybe_charge(task)
        resources = self._resources(task)
        started = datetime.now(UTC)
        if not self._acquire(task["id"], resources):
            mode = self.features.snapshot().get("resource_mutex_on_conflict", "queue")
            waited = (datetime.now(UTC) - started).total_seconds() * 1000
            self.metrics.mutex_wait_ms.append(waited)
            if mode == "fail":
                self._fail(task, "CONFLICT_MUTEX", "资源被占用")
            return False
        task["status"] = "Running"
        self._append(task, "已获取资源锁并开始执行")
        self.repo.save_task(task)
        self.metrics.dispatch_latency_ms.append((datetime.now(UTC) - _parse(task["created_at"])).total_seconds() * 1000)
        self.hub.publish("task", {"id": task["id"], "status": "Running", "robot_id": task["robot_id"]})
        return True

    def _maybe_charge(self, task: dict) -> None:
        threshold = float(self.features.snapshot().get("low_battery_pct", self.settings.low_battery_pct))
        amr = self.registry.amr(task["robot_id"])
        status = amr.get_status()
        if status.battery_pct is None or status.battery_pct >= threshold:
            return
        if any(skill.get("type") == "dock_charge" for skill in task["skills"]):
            return
        charger = self.registry.robot_configs[task["robot_id"]].get("charger_id", f"charger-{task['robot_id']}")
        task["skills"].insert(0, {"type": "dock_charge", "params": {"charger_id": charger}})
        with self.repo.session() as session:
            from app.adapters.orm import TaskRow

            row = session.get(TaskRow, task["id"])
            if row is not None:
                row.skills_json = json.dumps(task["skills"], ensure_ascii=False)
                session.commit()

    def _resources(self, task: dict) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        charger_default = self.registry.robot_configs[task["robot_id"]].get("charger_id", f"charger-{task['robot_id']}")
        for skill in task["skills"]:
            params = skill.get("params") or {}
            kind = skill.get("type")
            if params.get("zone_id"):
                found.append(("zone", params["zone_id"]))
            if kind in {"call_elevator", "enter_elevator", "exit_elevator", "elevator_transfer"} and params.get("elevator_id"):
                found.append(("elevator", params["elevator_id"]))
            if kind == "dock_charge":
                found.append(("charger", params.get("charger_id") or charger_default))
            if params.get("point_id"):
                found.append(("point", params["point_id"]))
            if params.get("enter_point_id"):
                found.append(("point", params["enter_point_id"]))
        unique = list(dict.fromkeys(found))
        unique.sort(key=lambda item: LOCK_ORDER[item[0]])
        return unique

    def _acquire(self, holder: str, resources: list[tuple[str, str]]) -> bool:
        expires = utcnow() + timedelta(seconds=self.settings.lock_ttl_sec)
        acquired: list[tuple[str, str]] = []
        for resource_type, resource_id in resources:
            ok = self.repo.insert_lock(resource_type, resource_id, holder, expires)
            if not ok:
                self.repo.delete_locks_for_holder(holder)
                return False
            acquired.append((resource_type, resource_id))
        _ = acquired
        return True

    def _step(self, task: dict) -> None:
        token_task = task_id_var.set(task["id"])
        token_robot = robot_id_var.set(task["robot_id"])
        try:
            fresh = self.repo.get_task(task["id"])
            if fresh["status"] != "Running":
                return
            self._guard_robot(fresh)
            skills = fresh["skills"]
            index = fresh["skill_index"]
            if index >= len(skills):
                self._succeed(fresh)
                return
            skill = skills[index]
            self._run_skill(fresh, skill, index)
            fresh["skill_index"] = index + 1
            self._append(fresh, f"技能完成 {skill.get('type')}")
            self.repo.save_task(fresh)
            self.metrics.command_ok += 1
            if fresh["skill_index"] >= len(skills):
                self._succeed(self.repo.get_task(fresh["id"]))
        except AppError as exc:
            self.metrics.command_fail += 1
            current = self.repo.get_task(task["id"])
            if current["status"] == "Running":
                self._fail(current, exc.code, exc.message)
        finally:
            task_id_var.reset(token_task)
            robot_id_var.reset(token_robot)

    def _guard_robot(self, task: dict) -> None:
        status = self.registry.amr(task["robot_id"]).get_status()
        if not status.online:
            raise device_offline(f"{task['robot_id']} 离线")
        if status.estop or status.mode in {"estop", "fault"}:
            code = "ESTOP" if status.estop or status.mode == "estop" else "FAULT"
            raise AppError(code, status.fault_msg or "急停或故障，拒绝继续执行", retryable=False, status_code=409)

    def _run_skill(self, task: dict, skill: dict, index: int) -> None:
        kind = skill["type"]
        params = skill.get("params") or {}
        amr = self.registry.amr(task["robot_id"])
        if kind == "wait":
            seconds = float(params.get("seconds") or 0)
            if seconds > 0:
                time.sleep(seconds)
            return
        if kind == "navigate_to":
            point = self.repo.get_point(params["point_id"])
            pose = pose_from_dict(point["pose"])
            pose.map_id = point["map_id"]
            handle = amr.navigate_to(point_id=point["id"], pose=pose)
            self._handle(handle)
            self.hub.publish("pose", {"robot_id": task["robot_id"], "pose": amr.get_status().pose.to_dict()})
            return
        if kind == "dock_charge":
            self._handle(amr.dock_charge())
            return
        if kind == "sample_particle":
            self._sample_particle(task, params, index)
            return
        if kind == "read_climate":
            self._sample_climate(task, params, index)
            return
        if kind == "read_airflow":
            self._sample_airflow(task, params, index)
            return
        if kind in {"call_elevator", "enter_elevator", "exit_elevator", "elevator_transfer"}:
            self._elevator(task, kind, params)
            return
        raise validation_error(f"未实现技能 {kind}")

    def _elevator(self, task: dict, kind: str, params: dict) -> None:
        if not self.features.snapshot().get("elevator_skills", True):
            raise validation_error("电梯技能已关闭")
        elevator = self.registry.elevator(params["elevator_id"])
        if kind == "call_elevator":
            self._handle(elevator.call_elevator(int(params["floor"])))
            return
        if kind == "enter_elevator":
            self._handle(elevator.enter_elevator())
            return
        if kind == "exit_elevator":
            self._handle(elevator.exit_elevator({"floor": int(params.get("floor", elevator.get_status().current_floor or 1))}))
            return
        floor = int(params["to_floor"])
        self._handle(elevator.call_elevator(floor))
        if params.get("enter_point_id"):
            point = self.repo.get_point(params["enter_point_id"])
            pose = pose_from_dict(point["pose"])
            pose.map_id = point["map_id"]
            self._handle(self.registry.amr(task["robot_id"]).navigate_to(point["id"], pose))
        self._handle(elevator.enter_elevator())
        self._handle(elevator.exit_elevator({"floor": floor}))

    def _sample_particle(self, task: dict, params: dict, index: int) -> None:
        instrument = self.registry.instrument_for(task["robot_id"], "particle")
        try:
            handle, _ = read_with_retry(lambda: instrument.start_sample(params), self.settings.adapter_max_attempts)
            self._handle(handle)
            channels, retried = read_with_retry(instrument.read_channels, self.settings.adapter_max_attempts)
        except AppError:
            self._store(task, params.get("point_id"), instrument.device_id, index, "particle.sample", None, "counts", "bad")
            raise
        self._handle(instrument.stop_sample())
        quality = "uncertain" if retried else "good"
        for channel in channels:
            metric = f"particle.{channel.channel}um"
            self._store(task, params.get("point_id"), instrument.device_id, index, metric, channel.value, channel.unit, quality)

    def _sample_climate(self, task: dict, params: dict, index: int) -> None:
        instrument = self.registry.instrument_for(task["robot_id"], "climate")
        try:
            reading, retried = read_with_retry(instrument.read_temp_humidity, self.settings.adapter_max_attempts)
        except AppError:
            self._store(task, params.get("point_id"), instrument.device_id, index, "temp_c", None, "C", "bad")
            raise
        quality = "uncertain" if retried else "good"
        self._store(task, params.get("point_id"), instrument.device_id, index, "temp_c", reading.temp_c, "C", quality)
        self._store(task, params.get("point_id"), instrument.device_id, index, "humidity_rh", reading.humidity_rh, "%RH", quality)

    def _sample_airflow(self, task: dict, params: dict, index: int) -> None:
        instrument = self.registry.instrument_for(task["robot_id"], "airflow")
        try:
            reading, retried = read_with_retry(instrument.read_air_speed, self.settings.adapter_max_attempts)
        except AppError:
            self._store(task, params.get("point_id"), instrument.device_id, index, "air_speed_mps", None, "m/s", "bad")
            raise
        quality = "uncertain" if retried else "good"
        self._store(task, params.get("point_id"), instrument.device_id, index, "air_speed_mps", reading.speed_mps, reading.unit, quality)

    def _store(self, task, point_id, device_id, index, metric, value, unit, quality) -> None:
        ts = utcnow()
        sample_id = f"{task['id']}:{index}:{metric}"
        key = idempotency_key(client_request_id=None, device_id=device_id, sample_id=sample_id, ts_iso=ts.isoformat())
        measurement, replay = self.repo.insert_measurement(
            idempotency_key=key,
            task_id=task["id"],
            point_id=point_id,
            robot_id=task["robot_id"],
            device_id=device_id,
            metric=metric,
            value=value,
            unit=unit,
            quality=quality,
            ts=ts,
        )
        if not replay:
            self.hub.publish("measurement", measurement)
            self._evaluate_limit(task, point_id, metric, value, measurement["id"])

    def evaluate_measurement(self, measurement: dict) -> None:
        """补传路径与调度采样共用限值判断。"""
        task = {
            "id": measurement.get("task_id"),
            "robot_id": measurement.get("robot_id") or measurement.get("device_id") or "ingest",
        }
        self._evaluate_limit(task, measurement.get("point_id"), measurement.get("metric"), measurement.get("value"), measurement["id"])

    def _evaluate_limit(self, task, point_id, metric, value, measurement_id: str) -> None:
        if value is None or not point_id:
            return
        point = self.repo.get_point(point_id)
        rule = (point.get("limits") or {}).get(metric)
        if not rule:
            return
        breached = False
        if "max" in rule and value > float(rule["max"]):
            breached = True
        if "min" in rule and value < float(rule["min"]):
            breached = True
        if not breached:
            return
        alarm = self.repo.add_alarm(
            rule_id=f"limit.{metric}",
            severity="warning",
            state="open",
            source=task["robot_id"],
            message=f"{point_id} {metric}={value} 超限",
            object_ref=measurement_id,
            ack_by=None,
            note="",
        )
        self.hub.publish("alarm", alarm)

    def _succeed(self, task: dict) -> None:
        task["status"] = "Succeeded"
        self._append(task, "任务成功")
        self.repo.save_task(task)
        self.repo.delete_locks_for_holder(task["id"])
        self.hub.publish("task", {"id": task["id"], "status": "Succeeded", "robot_id": task["robot_id"]})
        from app.services.reports import generate_task_report

        generate_task_report(self.repo, self.settings, task["id"])

    def _fail(self, task: dict, code: str, message: str) -> None:
        if task["status"] in TERMINAL:
            return
        task["status"] = "Failed"
        task["error_code"] = code
        task["error_message"] = message
        self._append(task, f"失败 {code}: {message}")
        self.repo.save_task(task)
        self.repo.delete_locks_for_holder(task["id"])
        self.hub.publish("task", {"id": task["id"], "status": "Failed", "error_code": code})
        if code in {"ESTOP", "FAULT", "DEVICE_OFFLINE"}:
            rule_id = "device.offline" if code == "DEVICE_OFFLINE" else f"device.{code.lower()}"
            alarm = self.repo.add_alarm(
                rule_id=rule_id,
                severity="critical",
                state="open",
                source=task["robot_id"],
                message=message,
                object_ref=task["id"],
                ack_by=None,
                note="",
            )
            self.hub.publish("alarm", alarm)
        log.warning("task failed code=%s", code)
        on_fail = task.get("on_fail") or "none"
        if on_fail == "dock_charge":
            try:
                self.registry.amr(task["robot_id"]).dock_charge()
            except AppError:
                log.warning("fail dock skipped")
        from app.services.reports import generate_task_report

        generate_task_report(self.repo, self.settings, task["id"])

    def _handle(self, handle) -> None:
        if handle.status != "done":
            raise AppError("DEVICE_OFFLINE", handle.detail or "命令失败", retryable=True, status_code=503)

    def _append(self, task: dict, message: str) -> None:
        task.setdefault("timeline", []).append({"ts": utcnow().isoformat(), "message": message})

    def _refresh_parents(self) -> None:
        from app.services.reports import generate_summary_report

        for composite in self.repo.list_composites():
            children = [self.repo.get_task(child_id) for child_id in composite["child_ids"]]
            status = _rollup([child["status"] for child in children])
            if status != composite["status"]:
                self.repo.save_composite_status(composite["id"], status)
            if status in TERMINAL:
                generate_summary_report(self.repo, self.settings, composite["id"], "composite", composite["child_ids"])
        for cluster in self.repo.list_clusters():
            children = [self.repo.get_task(child_id) for child_id in cluster["child_ids"]]
            status = _rollup([child["status"] for child in children])
            if status != cluster["status"]:
                self.repo.save_cluster_status(cluster["id"], status)
            if status in TERMINAL:
                generate_summary_report(self.repo, self.settings, cluster["id"], "cluster", cluster["child_ids"])


def _rollup(statuses: list[str]) -> str:
    if not statuses:
        return "Queued"
    if any(status not in TERMINAL for status in statuses):
        if any(status == "Running" for status in statuses):
            return "Running"
        return "Queued"
    if all(status == "Succeeded" for status in statuses):
        return "Succeeded"
    if any(status == "Failed" for status in statuses):
        return "Failed"
    return "Cancelled"


def _parse(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def raise_if_mutex(code: str) -> None:
    if code == "CONFLICT_MUTEX":
        raise conflict_mutex()
