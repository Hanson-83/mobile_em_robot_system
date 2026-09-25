"""M1 内存仓储。M3 替换为 PostgreSQL。任务持久化细节待确认（URS-NFR-002）。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import ValidationError

from app.core.errors import not_found, validation_error
from app.domain.dto import (
    Alarm,
    AlarmState,
    ApprovalRequest,
    ApprovalState,
    Measurement,
    MeasurementIn,
    Point,
    Pose,
    Report,
    TaskCreate,
    TaskInstance,
    TaskState,
)
from app.services.idempotency import make_idempotency_key


class MemoryStores:
    def __init__(self) -> None:
        self.tasks: dict[str, TaskInstance] = {}
        self.points: dict[str, Point] = {
            "P1": Point(id="P1", name="洁净走廊-1", pose=Pose(x=2.0, y=1.0, map_id="map-01")),
        }
        self.measurements: dict[str, Measurement] = {}
        self.by_idem: dict[str, str] = {}
        self.alarms: dict[str, Alarm] = {}
        self.approvals: dict[str, ApprovalRequest] = {}
        self.reports: dict[str, Report] = {}
        self.users: list[dict[str, str]] = []
        self.maps: list[dict[str, str]] = [
            {"id": "map-01", "name": "占位地图", "source": "placeholder"},
        ]
        self.limits: dict[str, float] = {"particle.0.5um": 3520.0}

    def create_task(self, body: TaskCreate) -> TaskInstance:
        task = TaskInstance(
            id=str(uuid.uuid4()),
            name=body.name,
            robot_id=body.robot_id,
            skills=body.skills,
            state=TaskState.CREATED,
        )
        self.tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> TaskInstance:
        task = self.tasks.get(task_id)
        if not task:
            raise not_found(f"任务不存在: {task_id}")
        return task

    def cancel_task(self, task_id: str) -> TaskInstance:
        task = self.get_task(task_id)
        if task.state in {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}:
            raise validation_error(f"终态不可取消: {task.state}")
        task.state = TaskState.CANCELLED
        return task

    def upsert_measurement(self, body: MeasurementIn) -> Measurement:
        key = make_idempotency_key(
            device_id=body.device_id,
            sample_id=body.sample_id,
            ts=body.ts,
            client_request_id=body.client_request_id,
        )
        existing_id = self.by_idem.get(key)
        if existing_id:
            found = self.measurements[existing_id]
            return found.model_copy(update={"replay": True})
        item = Measurement(
            id=str(uuid.uuid4()),
            idempotency_key=key,
            **body.model_dump(),
        )
        self.measurements[item.id] = item
        self.by_idem[key] = item.id
        return item

    def create_point(self, point: Point) -> Point:
        if point.id in self.points:
            raise validation_error(f"点位已存在: {point.id}")
        self.points[point.id] = point
        return point

    def update_point(self, point_id: str, patch: dict) -> Point:
        point = self.points.get(point_id)
        if not point:
            raise not_found(f"点位不存在: {point_id}")
        if "id" in patch and patch["id"] != point_id:
            raise validation_error("点位 id 不可修改")
        merged = point.model_dump()
        merged.update({k: v for k, v in patch.items() if k != "id"})
        try:
            updated = Point.model_validate(merged)
        except ValidationError as exc:
            raise validation_error("点位字段非法", details={"errors": exc.errors()}) from exc
        self.points[point_id] = updated
        return updated

    def delete_point(self, point_id: str) -> None:
        if point_id not in self.points:
            raise not_found(f"点位不存在: {point_id}")
        referenced = any(
            any(s.params.get("point_id") == point_id for s in t.skills) for t in self.tasks.values()
        )
        if referenced:
            raise validation_error(f"点位仍被任务引用: {point_id}")
        del self.points[point_id]

    def ack_alarm(self, alarm_id: str, actor: str) -> Alarm:
        alarm = self.alarms.get(alarm_id)
        if not alarm:
            raise not_found(f"报警不存在: {alarm_id}")
        alarm.state = AlarmState.ACKED
        alarm.ack_by = actor
        return alarm

    def close_alarm(self, alarm_id: str, actor: str) -> Alarm:
        alarm = self.ack_alarm(alarm_id, actor)
        alarm.state = AlarmState.CLOSED
        return alarm

    def create_approval(self, object_ref: str, action: str, payload: dict) -> ApprovalRequest:
        req = ApprovalRequest(
            id=str(uuid.uuid4()),
            object_ref=object_ref,
            action=action,
            payload=payload,
            state=ApprovalState.PENDING,
        )
        self.approvals[req.id] = req
        return req

    def decide_approval(self, approval_id: str, approve: bool) -> ApprovalRequest:
        req = self.approvals.get(approval_id)
        if not req:
            raise not_found(f"批准单不存在: {approval_id}")
        req.state = ApprovalState.APPROVED if approve else ApprovalState.REJECTED
        return req

    def add_report(self, task_ref: str) -> Report:
        report = Report(
            id=str(uuid.uuid4()),
            task_ref=task_ref,
            file_uri=f"memory://reports/{task_ref}.html",
            format="html",
            generated_at=datetime.now(UTC),
        )
        self.reports[report.id] = report
        return report
