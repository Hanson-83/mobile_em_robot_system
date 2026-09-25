"""Gateway 路由。分组：operations / data / settings。"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.adapters.repository import ensure_naive, utcnow
from app.core.errors import AppError, approval_required, auth_required, forbidden, validation_error
from app.core.security import decode_token, hash_password, hash_token, issue_token, verify_password
from app.services.backup import create_backup, restore_backup
from app.services.support import audit, idempotency_key

operations = APIRouter(prefix="/api/v1", tags=["operations"])
data = APIRouter(prefix="/api/v1", tags=["data"])
settings_router = APIRouter(prefix="/api/v1", tags=["settings"])


class LoginIn(BaseModel):
    username: str
    password: str


class TaskIn(BaseModel):
    robot_id: str
    point_id: str | None = None
    skills: list[dict] | None = None
    on_fail: str = "none"
    client_request_id: str | None = None
    wait_seconds: float | None = None


class CompositeIn(BaseModel):
    name: str
    children: list[TaskIn]


class ClusterIn(BaseModel):
    name: str
    items: list[TaskIn]


class PointIn(BaseModel):
    id: str
    map_id: str
    name: str
    pose: dict
    instrument_profile: str = "particle+climate+airflow"
    limits: dict = Field(default_factory=dict)


class MapIn(BaseModel):
    id: str
    name: str
    source: str = "import"
    width_m: float = 20
    height_m: float = 15
    meta: dict = Field(default_factory=dict)
    points: list[PointIn] = Field(default_factory=list)


class LimitPatch(BaseModel):
    point_id: str
    limits: dict


class MeasurementIn(BaseModel):
    device_id: str
    sample_id: str
    metric: str
    unit: str
    value: float | None = None
    quality: str = "good"
    ts: str | None = None
    task_id: str | None = None
    point_id: str | None = None
    robot_id: str | None = None
    client_request_id: str | None = None
    idempotency_key: str | None = None


class AlarmNote(BaseModel):
    note: str = ""


class UserIn(BaseModel):
    username: str
    password: str
    display_name: str = ""
    roles: list[str] = Field(default_factory=lambda: ["viewer"])


class GroupIn(BaseModel):
    name: str
    user_ids: list[str] = Field(default_factory=list)
    role_name: str = ""


class GroupPatch(BaseModel):
    role_name: str | None = None
    user_ids: list[str] | None = None


class RolePermIn(BaseModel):
    permissions: list[str]


class FeaturePatch(BaseModel):
    audit_trail: bool | None = None
    e_sign: bool | None = None
    elevator_skills: bool | None = None
    resource_mutex: str | None = None
    realtime_channel: str | None = None
    resource_mutex_on_conflict: str | None = None
    measurement_write_missing: bool | None = None
    fail_on_disconnect: bool | None = None
    low_battery_pct: float | None = None
    auto_backup_interval_minutes: float | None = None


class ApprovalDecision(BaseModel):
    password: str
    meaning: str


class Principal(BaseModel):
    user_id: str
    username: str
    permissions: set[str]
    kind: str

    model_config = {"arbitrary_types_allowed": True}


def runtime_of(request):
    return request.app.state.runtime


def current_principal(request: Request) -> Principal:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise auth_required()
    token = header.split(" ", 1)[1].strip()
    runtime = runtime_of(request)
    try:
        payload = decode_token(token, runtime.settings.secret_key)
    except ValueError:
        role = runtime.repo.role_for_api_token(hash_token(token))
        if role is None:
            raise auth_required("令牌无效或已过期")
        perms = runtime.repo.permissions_for_roles([role])
        return Principal(user_id="api", username="api_client", permissions=set(perms), kind="api")
    return Principal(
        user_id=payload["sub"],
        username=payload["username"],
        permissions=set(payload.get("perms") or []),
        kind=payload.get("kind") or "session",
    )


def need(permission: str):
    def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if permission not in principal.permissions:
            raise forbidden(f"缺少权限 {permission}")
        return principal

    return dependency


@operations.post("/auth/login")
def login(body: LoginIn, request: Request):
    runtime = runtime_of(request)
    user = runtime.repo.get_user_by_name(body.username)
    if user is None or user.disabled or not verify_password(body.password, user.password_hash):
        raise auth_required("用户名或口令错误")
    roles = runtime.repo.roles_for_user(user.id)
    perms = runtime.repo.permissions_for_roles(roles)
    token = issue_token(
        subject=user.id,
        username=user.username,
        permissions=perms,
        secret=runtime.settings.secret_key,
        ttl_min=runtime.settings.session_ttl_min,
    )
    audit(runtime.repo, runtime.features, actor=user.username, action="auth.login", object_ref=user.username)
    return {"access_token": token, "token_type": "bearer", "username": user.username, "roles": roles, "permissions": perms}


@operations.get("/tasks")
def list_tasks(request: Request, _principal: Principal = Depends(need("operations.task.read"))):
    return {"items": runtime_of(request).repo.list_tasks()}


@operations.post("/tasks")
def create_task(body: TaskIn, request: Request, principal: Principal = Depends(need("operations.task.write"))):
    runtime = runtime_of(request)
    task, replay = runtime.scheduler.create_task(
        robot_id=body.robot_id,
        skills=body.skills,
        point_id=body.point_id,
        on_fail=body.on_fail,
        client_request_id=body.client_request_id,
    )
    if not replay:
        audit(runtime.repo, runtime.features, actor=principal.username, action="task.create", object_ref=task["id"], after=task)
    if replay:
        task = dict(task)
        task["idempotency_replay"] = True
        task["code"] = "IDEMPOTENCY_REPLAY"
    return task


@operations.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, request: Request, principal: Principal = Depends(need("operations.task.write"))):
    runtime = runtime_of(request)
    task = runtime.scheduler.cancel(task_id)
    audit(runtime.repo, runtime.features, actor=principal.username, action="task.cancel", object_ref=task_id)
    return task


@operations.post("/scheduler/dispatch")
def dispatch_tasks(request: Request, _principal: Principal = Depends(need("operations.task.write"))):
    count = runtime_of(request).scheduler.dispatch_available()
    return {"dispatched": count}


@operations.post("/scheduler/drain")
def drain_tasks(request: Request, _principal: Principal = Depends(need("operations.task.write"))):
    runtime_of(request).scheduler.drain()
    return {"ok": True}


@operations.post("/composites")
def create_composite(body: CompositeIn, request: Request, principal: Principal = Depends(need("operations.task.write"))):
    runtime = runtime_of(request)
    child_ids: list[str] = []
    previous = None
    composite_id = uuid.uuid4().hex
    for child in body.children:
        skills = list(child.skills) if child.skills else None
        if child.wait_seconds:
            if skills is None:
                if not child.point_id:
                    raise validation_error("等待步骤需要 point_id 或 skills")
                skills = runtime.scheduler.default_skills(child.point_id)
            skills = [{"type": "wait", "params": {"seconds": child.wait_seconds}}, *skills]
        task, _replay = runtime.scheduler.create_task(
            robot_id=child.robot_id,
            skills=skills,
            point_id=child.point_id,
            on_fail=child.on_fail,
            client_request_id=child.client_request_id,
            composite_id=composite_id,
            depends_on=previous,
        )
        child_ids.append(task["id"])
        previous = task["id"]
    composite = runtime.repo.add_composite(composite_id, body.name, child_ids)
    audit(runtime.repo, runtime.features, actor=principal.username, action="composite.create", object_ref=composite["id"])
    return composite


@operations.post("/clusters")
def create_cluster(body: ClusterIn, request: Request, principal: Principal = Depends(need("operations.task.write"))):
    runtime = runtime_of(request)
    child_ids = []
    cluster_id = uuid.uuid4().hex
    for child in body.items:
        task, _replay = runtime.scheduler.create_task(
            robot_id=child.robot_id,
            skills=child.skills,
            point_id=child.point_id,
            on_fail=child.on_fail,
            client_request_id=child.client_request_id,
            cluster_id=cluster_id,
        )
        child_ids.append(task["id"])
    cluster = runtime.repo.add_cluster(cluster_id, body.name, child_ids)
    audit(runtime.repo, runtime.features, actor=principal.username, action="cluster.create", object_ref=cluster_id)
    return cluster


@operations.get("/composites")
def list_composites(request: Request, _principal: Principal = Depends(need("operations.task.read"))):
    return {"items": runtime_of(request).repo.list_composites()}


@operations.get("/clusters")
def list_clusters(request: Request, _principal: Principal = Depends(need("operations.task.read"))):
    return {"items": runtime_of(request).repo.list_clusters()}


@operations.post("/alarms/{alarm_id}/ack")
def ack_alarm(alarm_id: str, body: AlarmNote, request: Request, principal: Principal = Depends(need("operations.alarm.ack"))):
    alarm = runtime_of(request).repo.update_alarm(alarm_id, state="acked", ack_by=principal.username, note=body.note)
    audit(runtime_of(request).repo, runtime_of(request).features, actor=principal.username, action="alarm.ack", object_ref=alarm_id)
    return alarm


@operations.post("/alarms/{alarm_id}/close")
def close_alarm(alarm_id: str, body: AlarmNote, request: Request, principal: Principal = Depends(need("operations.alarm.close"))):
    current = runtime_of(request).repo.get_alarm(alarm_id)
    if current["state"] == "open":
        raise validation_error("请先确认再关闭")
    alarm = runtime_of(request).repo.update_alarm(alarm_id, state="closed", note=body.note, ack_by=current["ack_by"] or principal.username)
    audit(runtime_of(request).repo, runtime_of(request).features, actor=principal.username, action="alarm.close", object_ref=alarm_id)
    return alarm


@operations.get("/approvals")
def list_approvals(request: Request, state: str | None = None, _principal: Principal = Depends(need("operations.approval.read"))):
    runtime = runtime_of(request)
    items = []
    for item in runtime.repo.list_approvals(state):
        items.append(_refresh_approval(runtime, item))
    return {"items": items}


@operations.post("/approvals/{approval_id}/approve")
def approve(approval_id: str, body: ApprovalDecision, request: Request, principal: Principal = Depends(need("operations.approval.write"))):
    return _decide(request, approval_id, body, principal, approved=True)


@operations.post("/approvals/{approval_id}/reject")
def reject(approval_id: str, body: ApprovalDecision, request: Request, principal: Principal = Depends(need("operations.approval.write"))):
    return _decide(request, approval_id, body, principal, approved=False)


@data.get("/measurements")
def list_measurements(
    request: Request,
    task_id: str | None = None,
    point_id: str | None = None,
    metric: str | None = None,
    since: str | None = None,
    until: str | None = None,
    _principal: Principal = Depends(need("data.measurement.read")),
):
    from datetime import datetime

    def parse(value: str | None):
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    items = runtime_of(request).repo.list_measurements(
        task_id=task_id, point_id=point_id, metric=metric, since=parse(since), until=parse(until)
    )
    return {"items": items}


@data.post("/measurements")
def ingest_measurement(body: MeasurementIn, request: Request, _principal: Principal = Depends(need("data.measurement.write"))):
    runtime = runtime_of(request)
    ts = utcnow()
    if body.ts:
        from datetime import datetime

        ts = datetime.fromisoformat(body.ts.replace("Z", "+00:00"))
    key = body.idempotency_key or idempotency_key(
        client_request_id=body.client_request_id,
        device_id=body.device_id,
        sample_id=body.sample_id,
        ts_iso=ts.isoformat(),
    )
    if body.task_id and body.point_id:
        task = runtime.repo.get_task(body.task_id)
        skills = task["skills"]
        referenced = set()
        for skill in skills:
            params = skill.get("params") or {}
            if params.get("point_id"):
                referenced.add(params["point_id"])
        if referenced and body.point_id not in referenced:
            raise validation_error("点位不属于该任务")
    measurement, replay = runtime.repo.insert_measurement(
        idempotency_key=key,
        task_id=body.task_id,
        point_id=body.point_id,
        robot_id=body.robot_id,
        device_id=body.device_id,
        metric=body.metric,
        value=body.value,
        unit=body.unit,
        quality=body.quality,
        ts=ts,
    )
    if replay:
        measurement = dict(measurement)
        measurement["idempotency_replay"] = True
        measurement["code"] = "IDEMPOTENCY_REPLAY"
    else:
        runtime.hub.publish("measurement", measurement)
        runtime.scheduler.evaluate_measurement(measurement)
    return measurement


@data.get("/alarms")
def list_alarms(
    request: Request,
    state: str | None = None,
    severity: str | None = None,
    _principal: Principal = Depends(need("data.alarm.read")),
):
    return {"items": runtime_of(request).repo.list_alarms(state=state, severity=severity)}


@data.get("/alarms/export")
def export_alarms(
    request: Request,
    state: str | None = None,
    severity: str | None = None,
    _principal: Principal = Depends(need("data.alarm.export")),
):
    rows = runtime_of(request).repo.list_alarms(state=state, severity=severity)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "ts", "severity", "state", "source", "rule_id", "message", "object_ref", "ack_by", "note"])
    for row in rows:
        writer.writerow([
            row["id"], row["ts"], row["severity"], row["state"], row["source"], row["rule_id"],
            row["message"], row["object_ref"], row["ack_by"] or "", row["note"],
        ])
    content = "\ufeff" + buffer.getvalue()
    return Response(content=content, media_type="text/csv; charset=utf-8")


@data.get("/reports")
def list_reports(request: Request, _principal: Principal = Depends(need("data.report.read"))):
    return {"items": runtime_of(request).repo.list_reports()}


@data.get("/reports/{report_id}")
def get_report(report_id: str, request: Request, _principal: Principal = Depends(need("data.report.read"))):
    report = runtime_of(request).repo.get_report(report_id)
    from pathlib import Path

    path = Path(report["file_uri"])
    report = dict(report)
    report["html"] = path.read_text(encoding="utf-8") if path.exists() else ""
    return report


@data.post("/reports/{report_id}/approve")
def approve_report(report_id: str, request: Request, principal: Principal = Depends(need("data.report.write"))):
    runtime = runtime_of(request)
    report = runtime.repo.get_report(report_id)
    if runtime.features.snapshot().get("e_sign"):
        approval = _create_approval(
            runtime,
            principal,
            action="approve_report",
            object_ref=f"report:{report_id}",
            payload={"report_id": report_id},
        )
        raise approval_required("报告批准需完成签名与批准流", {"approval_id": approval["id"]})
    return _mark_report(runtime, report["id"], principal.username)


@data.get("/robots")
def list_robots(request: Request, _principal: Principal = Depends(need("data.robot.read"))):
    runtime = runtime_of(request)
    runtime.scheduler.poll_devices()
    items = []
    for robot_id, amr in runtime.registry.amrs.items():
        config = runtime.registry.robot_configs[robot_id]
        status = amr.get_status().to_dict()
        items.append({
            "id": robot_id,
            "name": config.get("name", robot_id),
            "adapter_type": amr.adapter_type,
            "map_id": config.get("map_id"),
            "status": status,
        })
    return {"items": items}


@data.get("/maps")
def list_maps(request: Request, _principal: Principal = Depends(need("data.map.read"))):
    runtime = runtime_of(request)
    maps = []
    for item in runtime.repo.list_maps():
        item = dict(item)
        item["points"] = runtime.repo.list_points(item["id"])
        maps.append(item)
    return {"items": maps}


@data.get("/elevators")
def list_elevators(request: Request, _principal: Principal = Depends(need("data.robot.read"))):
    items = []
    for device_id, elevator in runtime_of(request).registry.elevators.items():
        status = elevator.get_status().to_dict()
        items.append({"id": device_id, "adapter_type": elevator.adapter_type, "status": status, "history": getattr(elevator, "history", [])})
    return {"items": items}


@data.get("/skills")
def list_skills(_principal: Principal = Depends(need("operations.task.read"))):
    return {
        "items": [
            {"type": "navigate_to", "phase": "mvp"},
            {"type": "dock_charge", "phase": "mvp"},
            {"type": "sample_particle", "phase": "mvp"},
            {"type": "read_climate", "phase": "mvp"},
            {"type": "read_airflow", "phase": "mvp"},
            {"type": "elevator_transfer", "phase": "mvp", "adapter": "ElevatorAdapter"},
            {"type": "call_elevator", "phase": "mvp", "adapter": "ElevatorAdapter"},
            {"type": "enter_elevator", "phase": "mvp", "adapter": "ElevatorAdapter"},
            {"type": "exit_elevator", "phase": "mvp", "adapter": "ElevatorAdapter"},
            {"type": "wait", "phase": "mvp"},
            {"type": "viable_sample", "phase": "extension", "adapter": "viable_placeholder"},
            {"type": "arm_sample", "phase": "future", "adapter": "arm_placeholder"},
        ]
    }


@data.get("/metrics")
def metrics(request: Request, _principal: Principal = Depends(need("settings.feature.read"))):
    runtime = runtime_of(request)
    online = sum(1 for device in runtime.registry.all_devices() if device.health().ok)
    return runtime.metrics.snapshot(online)


@settings_router.get("/points")
def list_points(request: Request, map_id: str | None = None, _principal: Principal = Depends(need("settings.point.read"))):
    return {"items": runtime_of(request).repo.list_points(map_id)}


@settings_router.post("/points")
def create_point(body: PointIn, request: Request, principal: Principal = Depends(need("settings.point.write"))):
    runtime = runtime_of(request)
    runtime.repo.get_map(body.map_id)
    point = runtime.repo.upsert_point(body.id, body.map_id, body.name, body.pose, body.instrument_profile, body.limits)
    audit(runtime.repo, runtime.features, actor=principal.username, action="point.upsert", object_ref=body.id, after=point)
    return point


@settings_router.delete("/points/{point_id}")
def delete_point(point_id: str, request: Request, principal: Principal = Depends(need("settings.point.write"))):
    runtime = runtime_of(request)
    if runtime.repo.point_referenced(point_id):
        raise validation_error("点位已被任务引用，不能删除")
    runtime.repo.delete_point(point_id)
    audit(runtime.repo, runtime.features, actor=principal.username, action="point.delete", object_ref=point_id)
    return {"deleted": point_id}


@settings_router.post("/maps")
def import_map(body: MapIn, request: Request, principal: Principal = Depends(need("settings.point.write"))):
    runtime = runtime_of(request)
    item = runtime.repo.upsert_map(body.id, body.name, body.source, body.width_m, body.height_m, body.meta)
    for point in body.points:
        runtime.repo.upsert_point(point.id, body.id, point.name, point.pose, point.instrument_profile, point.limits)
    audit(runtime.repo, runtime.features, actor=principal.username, action="map.import", object_ref=body.id)
    item["points"] = runtime.repo.list_points(body.id)
    return item


@settings_router.get("/settings/limits")
def get_limits(point_id: str, request: Request, _principal: Principal = Depends(need("settings.limit.read"))):
    point = runtime_of(request).repo.get_point(point_id)
    return {"point_id": point_id, "limits": point["limits"]}


@settings_router.patch("/settings/limits")
def patch_limits(body: LimitPatch, request: Request, principal: Principal = Depends(need("settings.limit.write"))):
    runtime = runtime_of(request)
    point = runtime.repo.get_point(body.point_id)
    if runtime.features.snapshot().get("e_sign"):
        approval = _create_approval(
            runtime,
            principal,
            action="update_limits",
            object_ref=f"point:{body.point_id}",
            payload={"point_id": body.point_id, "limits": body.limits},
        )
        raise approval_required("限值变更需完成签名与批准流", {"approval_id": approval["id"]})
    updated = runtime.repo.update_point_limits(body.point_id, body.limits)
    audit(
        runtime.repo,
        runtime.features,
        actor=principal.username,
        action="limits.update",
        object_ref=body.point_id,
        before=point["limits"],
        after=body.limits,
    )
    return updated


@settings_router.get("/settings/features")
def get_features(request: Request, _principal: Principal = Depends(need("settings.feature.read"))):
    return runtime_of(request).features.snapshot()


@settings_router.patch("/settings/features")
def patch_features(body: FeaturePatch, request: Request, principal: Principal = Depends(need("settings.feature.write"))):
    runtime = runtime_of(request)
    before = runtime.features.snapshot()
    patch = {key: value for key, value in body.model_dump().items() if value is not None}
    closing_audit = bool(before.get("audit_trail")) and patch.get("audit_trail") is False
    if closing_audit:
        audit(
            runtime.repo,
            runtime.features,
            actor=principal.username,
            action="features.update",
            object_ref="features",
            before=before,
            after={**before, **patch},
        )
    updated = runtime.features.update(patch)
    if not closing_audit:
        audit(runtime.repo, runtime.features, actor=principal.username, action="features.update", object_ref="features", before=before, after=updated)
    return updated


@settings_router.get("/users")
def list_users(request: Request, _principal: Principal = Depends(need("settings.user.read"))):
    return {"items": runtime_of(request).repo.list_users()}


@settings_router.post("/users")
def create_user(body: UserIn, request: Request, principal: Principal = Depends(need("settings.user.write"))):
    runtime = runtime_of(request)
    if len(body.password) < runtime.settings.password_min_len:
        raise validation_error(f"口令长度至少 {runtime.settings.password_min_len}")
    if runtime.repo.get_user_by_name(body.username):
        raise validation_error("用户已存在")
    user = runtime.repo.create_user(body.username, hash_password(body.password), body.display_name, body.roles)
    audit(runtime.repo, runtime.features, actor=principal.username, action="user.create", object_ref=body.username)
    return user


@settings_router.get("/groups")
def list_groups(request: Request, _principal: Principal = Depends(need("settings.user.read"))):
    return {"items": runtime_of(request).repo.list_groups()}


@settings_router.post("/groups")
def create_group(body: GroupIn, request: Request, principal: Principal = Depends(need("settings.user.write"))):
    runtime = runtime_of(request)
    group = runtime.repo.create_group(body.name, body.user_ids, body.role_name)
    audit(runtime.repo, runtime.features, actor=principal.username, action="group.create", object_ref=group["id"])
    return group


@settings_router.patch("/groups/{group_id}")
def patch_group(group_id: str, body: GroupPatch, request: Request, principal: Principal = Depends(need("settings.user.write"))):
    runtime = runtime_of(request)
    group = runtime.repo.update_group(group_id, body.role_name, body.user_ids)
    audit(runtime.repo, runtime.features, actor=principal.username, action="group.update", object_ref=group_id, after=group)
    return group


@settings_router.patch("/roles/{role_name}")
def patch_role(role_name: str, body: RolePermIn, request: Request, principal: Principal = Depends(need("settings.user.write"))):
    from app.services.bootstrap import ALL_PERMISSIONS

    runtime = runtime_of(request)
    unknown = sorted(set(body.permissions) - set(ALL_PERMISSIONS))
    if unknown:
        raise validation_error(f"未知权限 {unknown}")
    if role_name == "admin" and "settings.user.write" not in body.permissions:
        raise validation_error("管理员必须保留用户管理权限")
    permissions = runtime.repo.replace_role_permissions(role_name, body.permissions)
    audit(runtime.repo, runtime.features, actor=principal.username, action="role.permissions", object_ref=role_name, after={"permissions": permissions})
    return {"name": role_name, "permissions": permissions}


@settings_router.get("/audit")
def list_audit(request: Request, _principal: Principal = Depends(need("settings.audit.read"))):
    return {"items": runtime_of(request).repo.list_audits()}


@settings_router.post("/backups")
def backup_now(request: Request, principal: Principal = Depends(need("settings.backup.write"))):
    info = create_backup(runtime_of(request))
    audit(runtime_of(request).repo, runtime_of(request).features, actor=principal.username, action="backup.create", object_ref=info["id"])
    return info


@settings_router.get("/backups")
def list_backups(request: Request, _principal: Principal = Depends(need("settings.backup.read"))):
    return {"items": runtime_of(request).repo.list_backups()}


@settings_router.post("/backups/{backup_id}/restore")
def restore(backup_id: str, request: Request, principal: Principal = Depends(need("settings.backup.write"))):
    result = restore_backup(runtime_of(request), backup_id)
    audit(runtime_of(request).repo, runtime_of(request).features, actor=principal.username, action="backup.restore", object_ref=backup_id)
    return result


def _create_approval(runtime, principal: Principal, action: str, object_ref: str, payload: dict) -> dict:
    hours = runtime.settings.approval_ttl_hours
    expires = utcnow() + timedelta(hours=hours) if hours > 0 else utcnow() - timedelta(seconds=1)
    approval = runtime.repo.add_approval(
        object_ref=object_ref,
        action=action,
        payload_json=json.dumps(payload, ensure_ascii=False),
        state="Pending",
        requester=principal.username,
        approver=None,
        comment="",
        expires_at=expires,
    )
    runtime.hub.publish("approval", approval)
    return approval


def _refresh_approval(runtime, approval: dict) -> dict:
    if approval["state"] != "Pending":
        return approval
    from datetime import datetime

    expires = ensure_naive(datetime.fromisoformat(approval["expires_at"]))
    if expires <= utcnow():
        approval["state"] = "Expired"
        return runtime.repo.save_approval(approval)
    return approval


def _decide(request: Request, approval_id: str, body: ApprovalDecision, principal: Principal, approved: bool) -> dict:
    runtime = runtime_of(request)
    if principal.kind != "session":
        raise forbidden("电子签名需要用户会话")
    user = runtime.repo.get_user(principal.user_id)
    if user is None or not verify_password(body.password, user.password_hash):
        raise auth_required("签名口令不正确")
    approval = _refresh_approval(runtime, runtime.repo.get_approval(approval_id))
    if approval["state"] == "Expired":
        raise AppError("APPROVAL_REJECTED", "批准请求已过期", retryable=False, status_code=409)
    if approval["state"] != "Pending":
        raise validation_error("当前状态不可审批")
    new_state = "Approved" if approved else "Rejected"

    def apply(session):
        if not approved:
            return
        from app.adapters.orm import PointRow, ReportRow

        payload = approval["payload"]
        if approval["action"] == "update_limits":
            point = session.get(PointRow, payload["point_id"])
            if point is None:
                raise validation_error("点位不存在")
            point.limits_json = json.dumps(payload["limits"], ensure_ascii=False)
        elif approval["action"] == "approve_report":
            report = session.get(ReportRow, payload["report_id"])
            if report is None:
                raise validation_error("报告不存在")
            summary = json.loads(report.summary_json or "{}")
            summary["approved"] = True
            summary["approved_by"] = principal.username
            report.summary_json = json.dumps(summary, ensure_ascii=False)

    saved = runtime.repo.commit_decision(
        approval["id"],
        new_state,
        principal.username,
        body.meaning,
        principal.user_id,
        body.meaning,
        approval["object_ref"],
        apply,
    )
    if approved and approval["action"] == "approve_report":
        audit(
            runtime.repo,
            runtime.features,
            actor=principal.username,
            action="report.approve",
            object_ref=approval["payload"]["report_id"],
            after={"approved": True},
        )
    audit(
        runtime.repo,
        runtime.features,
        actor=principal.username,
        action="approval.approve" if approved else "approval.reject",
        object_ref=approval_id,
        after=saved,
    )
    runtime.hub.publish("approval", saved)
    return saved


def _mark_report(runtime, report_id: str, actor: str) -> dict:
    report = runtime.repo.get_report(report_id)
    summary = dict(report["summary"])
    summary["approved"] = True
    summary["approved_by"] = actor
    with runtime.repo.session() as session:
        from app.adapters.orm import ReportRow

        row = session.get(ReportRow, report_id)
        if row is None:
            raise validation_error("报告不存在")
        row.summary_json = json.dumps(summary, ensure_ascii=False)
        session.commit()
    audit(
        runtime.repo,
        runtime.features,
        actor=actor,
        action="report.approve",
        object_ref=report_id,
        before={"approved": False},
        after={"approved": True, "approved_by": actor},
    )
    return runtime.repo.get_report(report_id)


def register_routes(app: FastAPI) -> None:
    app.include_router(operations)
    app.include_router(data)
    app.include_router(settings_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready(request: Request):
        runtime = request.app.state.runtime
        adapters = []
        for device in runtime.registry.all_devices():
            item = device.health()
            adapters.append({"id": item.device_id, "ok": item.ok, "adapter": item.adapter, "detail": item.detail})
        secret_ok = runtime.settings.secret_key != "dev-only-change-me" or runtime.settings.allow_dev_secret
        db_ok = runtime.db_ok()
        body = {
            "db": db_ok,
            "secret_ok": secret_ok,
            "adapters": adapters,
            "degraded": any(not item["ok"] for item in adapters),
        }
        status = 200 if db_ok and secret_ok else 503
        return JSONResponse(content=body, status_code=status)

    @app.get("/api/v1/openapi.json", include_in_schema=False)
    def openapi_alias():
        return app.openapi()

    @app.websocket("/api/v1/ws")
    async def websocket_endpoint(websocket: WebSocket):
        token = websocket.query_params.get("token", "")
        runtime = websocket.app.state.runtime
        try:
            decode_token(token, runtime.settings.secret_key)
        except ValueError:
            if runtime.repo.role_for_api_token(hash_token(token)) is None:
                await websocket.close(code=4401)
                return
        await websocket.accept()
        await websocket.send_json({"topic": "hello", "payload": {"ok": True}})
        queue = runtime.hub.subscribe()
        try:
            message = await websocket.receive_json()
            topics = set(message.get("topics") or [])
            await websocket.send_json({"topic": "subscribed", "payload": {"topics": sorted(topics)}})
            sent: set[str] = set()
            for event in list(runtime.hub.events):
                if topics and event["topic"] not in topics:
                    continue
                sent.add(event["id"])
                await websocket.send_json(event)
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except TimeoutError:
                    await websocket.send_json({"topic": "heartbeat", "payload": {}})
                    continue
                if event["id"] in sent or (topics and event["topic"] not in topics):
                    continue
                await websocket.send_json(event)
        except Exception:
            return
        finally:
            runtime.hub.unsubscribe(queue)

