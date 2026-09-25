"""仓储。审计表只有插入与查询。"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.orm import (
    AlarmRow,
    ApiTokenRow,
    ApprovalRow,
    AuditRow,
    BackupRow,
    ClusterRow,
    CompositeRow,
    ESignRow,
    GroupMemberRow,
    GroupRow,
    KvRow,
    LockRow,
    MapRow,
    MeasurementRow,
    PointRow,
    ReportRow,
    RolePermissionRow,
    RoleRow,
    TaskRow,
    UserRoleRow,
    UserRow,
)
from app.core.errors import not_found
from app.domain.dto import Pose


def utcnow() -> datetime:
    """UTC 朴素时间。SQLite 读回后不保留时区，比较必须与之同型。"""
    return datetime.now(UTC).replace(tzinfo=None)


def ensure_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _loads(text: str | None, fallback):
    if not text:
        return fallback
    return json.loads(text)


class Repository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def session(self) -> Session:
        return self.session_factory()

    def get_user_by_name(self, username: str) -> UserRow | None:
        with self.session() as session:
            return session.scalar(select(UserRow).where(UserRow.username == username))

    def get_user(self, user_id: str) -> UserRow | None:
        with self.session() as session:
            return session.get(UserRow, user_id)

    def list_users(self) -> list[dict]:
        with self.session() as session:
            users = session.scalars(select(UserRow).order_by(UserRow.username)).all()
            result = []
            for user in users:
                roles = session.scalars(select(UserRoleRow.role_name).where(UserRoleRow.user_id == user.id)).all()
                result.append(self._user_dict(user, list(roles)))
            return result

    def create_user(self, username: str, password_hash: str, display_name: str, roles: list[str]) -> dict:
        with self.session() as session:
            user = UserRow(
                id=uuid.uuid4().hex,
                username=username,
                password_hash=password_hash,
                display_name=display_name,
            )
            session.add(user)
            for role in roles:
                session.add(UserRoleRow(user_id=user.id, role_name=role))
            session.commit()
            return self._user_dict(user, roles)

    def permissions_for_roles(self, roles: list[str]) -> list[str]:
        with self.session() as session:
            rows = session.scalars(select(RolePermissionRow).where(RolePermissionRow.role_name.in_(roles))).all()
            return sorted({row.permission for row in rows})

    def roles_for_user(self, user_id: str) -> list[str]:
        """直接角色，再加上所属用户组绑定的角色。"""
        with self.session() as session:
            direct = list(session.scalars(select(UserRoleRow.role_name).where(UserRoleRow.user_id == user_id)).all())
            group_ids = list(session.scalars(select(GroupMemberRow.group_id).where(GroupMemberRow.user_id == user_id)).all())
            group_roles: list[str] = []
            if group_ids:
                group_roles = [
                    role
                    for role in session.scalars(select(GroupRow.role_name).where(GroupRow.id.in_(group_ids))).all()
                    if role
                ]
            return list(dict.fromkeys([*direct, *group_roles]))

    def replace_role_permissions(self, role_name: str, permissions: list[str]) -> list[str]:
        with self.session() as session:
            if session.get(RoleRow, role_name) is None:
                raise not_found(f"角色 {role_name} 不存在")
            existing = session.scalars(select(RolePermissionRow).where(RolePermissionRow.role_name == role_name)).all()
            for row in existing:
                session.delete(row)
            for permission in sorted(set(permissions)):
                session.add(RolePermissionRow(role_name=role_name, permission=permission))
            session.commit()
            return sorted(set(permissions))

    def ensure_role(self, name: str, permissions: list[str]) -> None:
        with self.session() as session:
            if session.get(RoleRow, name) is None:
                session.add(RoleRow(name=name))
            existing = set(
                session.scalars(select(RolePermissionRow.permission).where(RolePermissionRow.role_name == name)).all()
            )
            for permission in permissions:
                if permission not in existing:
                    session.add(RolePermissionRow(role_name=name, permission=permission))
            session.commit()

    def ensure_user(self, username: str, password_hash: str, display_name: str, roles: list[str]) -> str:
        with self.session() as session:
            user = session.scalar(select(UserRow).where(UserRow.username == username))
            if user is None:
                user = UserRow(
                    id=uuid.uuid4().hex,
                    username=username,
                    password_hash=password_hash,
                    display_name=display_name,
                )
                session.add(user)
                session.flush()
            for role in roles:
                exists = session.scalar(
                    select(UserRoleRow).where(UserRoleRow.user_id == user.id, UserRoleRow.role_name == role)
                )
                if exists is None:
                    session.add(UserRoleRow(user_id=user.id, role_name=role))
            session.commit()
            return user.id

    def ensure_api_token(self, name: str, token_hash: str, role_name: str) -> None:
        with self.session() as session:
            row = session.scalar(select(ApiTokenRow).where(ApiTokenRow.token_hash == token_hash))
            if row is None:
                session.add(ApiTokenRow(id=uuid.uuid4().hex, name=name, token_hash=token_hash, role_name=role_name))
                session.commit()

    def role_for_api_token(self, token_hash: str) -> str | None:
        with self.session() as session:
            row = session.scalar(select(ApiTokenRow).where(ApiTokenRow.token_hash == token_hash))
            return row.role_name if row else None

    def get_kv(self, key: str) -> dict | None:
        with self.session() as session:
            row = session.get(KvRow, key)
            if row is None:
                return None
            return _loads(row.value_json, {})

    def put_kv(self, key: str, value: dict) -> None:
        with self.session() as session:
            row = session.get(KvRow, key)
            if row is None:
                session.add(KvRow(key=key, value_json=json.dumps(value, ensure_ascii=False)))
            else:
                row.value_json = json.dumps(value, ensure_ascii=False)
            session.commit()

    def upsert_map(self, map_id: str, name: str, source: str, width_m: float, height_m: float, meta: dict) -> dict:
        with self.session() as session:
            row = session.get(MapRow, map_id)
            if row is None:
                row = MapRow(id=map_id, name=name, source=source, width_m=width_m, height_m=height_m)
                session.add(row)
            row.name = name
            row.source = source
            row.width_m = width_m
            row.height_m = height_m
            row.meta_json = json.dumps(meta, ensure_ascii=False)
            session.commit()
            return self._map_dict(row)

    def list_maps(self) -> list[dict]:
        with self.session() as session:
            return [self._map_dict(row) for row in session.scalars(select(MapRow).order_by(MapRow.id)).all()]

    def get_map(self, map_id: str) -> dict:
        with self.session() as session:
            row = session.get(MapRow, map_id)
            if row is None:
                raise not_found(f"地图 {map_id} 不存在")
            return self._map_dict(row)

    def upsert_point(
        self,
        point_id: str,
        map_id: str,
        name: str,
        pose: dict,
        instrument_profile: str,
        limits: dict,
    ) -> dict:
        with self.session() as session:
            row = session.get(PointRow, point_id)
            if row is None:
                row = PointRow(id=point_id, map_id=map_id, name=name)
                session.add(row)
            row.map_id = map_id
            row.name = name
            row.pose_json = json.dumps(pose, ensure_ascii=False)
            row.instrument_profile = instrument_profile
            row.limits_json = json.dumps(limits, ensure_ascii=False)
            session.commit()
            return self._point_dict(row)

    def list_points(self, map_id: str | None = None) -> list[dict]:
        with self.session() as session:
            stmt = select(PointRow).order_by(PointRow.id)
            if map_id:
                stmt = stmt.where(PointRow.map_id == map_id)
            return [self._point_dict(row) for row in session.scalars(stmt).all()]

    def get_point(self, point_id: str) -> dict:
        with self.session() as session:
            row = session.get(PointRow, point_id)
            if row is None:
                raise not_found(f"点位 {point_id} 不存在")
            return self._point_dict(row)

    def update_point_limits(self, point_id: str, limits: dict) -> dict:
        with self.session() as session:
            row = session.get(PointRow, point_id)
            if row is None:
                raise not_found(f"点位 {point_id} 不存在")
            row.limits_json = json.dumps(limits, ensure_ascii=False)
            session.commit()
            return self._point_dict(row)

    def delete_point(self, point_id: str) -> None:
        with self.session() as session:
            row = session.get(PointRow, point_id)
            if row is None:
                raise not_found(f"点位 {point_id} 不存在")
            session.delete(row)
            session.commit()

    def point_referenced(self, point_id: str) -> bool:
        with self.session() as session:
            tasks = session.scalars(select(TaskRow)).all()
            for task in tasks:
                skills = _loads(task.skills_json, [])
                for skill in skills:
                    params = skill.get("params") or {}
                    if point_id in {params.get("point_id"), params.get("enter_point_id")}:
                        return True
            return False

    def add_task(self, **fields) -> dict:
        now = utcnow()
        with self.session() as session:
            row = TaskRow(created_at=now, updated_at=now, **fields)
            session.add(row)
            session.commit()
            return self._task_dict(row)

    def get_task_by_client_request(self, client_request_id: str) -> dict | None:
        with self.session() as session:
            row = session.scalar(select(TaskRow).where(TaskRow.client_request_id == client_request_id))
            return self._task_dict(row) if row else None

    def get_task(self, task_id: str) -> dict:
        with self.session() as session:
            row = session.get(TaskRow, task_id)
            if row is None:
                raise not_found(f"任务 {task_id} 不存在")
            return self._task_dict(row)

    def list_tasks(self, status: str | None = None) -> list[dict]:
        with self.session() as session:
            stmt = select(TaskRow).order_by(TaskRow.created_at)
            if status:
                stmt = stmt.where(TaskRow.status == status)
            return [self._task_dict(row) for row in session.scalars(stmt).all()]

    def save_task(self, task: dict) -> dict:
        with self.session() as session:
            row = session.get(TaskRow, task["id"])
            if row is None:
                raise not_found(f"任务 {task['id']} 不存在")
            row.status = task["status"]
            row.skill_index = task["skill_index"]
            row.error_code = task.get("error_code")
            row.error_message = task.get("error_message")
            row.timeline_json = json.dumps(task.get("timeline") or [], ensure_ascii=False)
            row.updated_at = utcnow()
            session.commit()
            return self._task_dict(row)

    def add_composite(self, composite_id: str, name: str, child_ids: list[str]) -> dict:
        with self.session() as session:
            row = CompositeRow(
                id=composite_id,
                name=name,
                status="Queued",
                child_ids_json=json.dumps(child_ids),
                created_at=utcnow(),
            )
            session.add(row)
            session.commit()
            return self._composite_dict(row)

    def list_composites(self) -> list[dict]:
        with self.session() as session:
            return [self._composite_dict(row) for row in session.scalars(select(CompositeRow)).all()]

    def save_composite_status(self, composite_id: str, status: str) -> None:
        with self.session() as session:
            row = session.get(CompositeRow, composite_id)
            if row:
                row.status = status
                session.commit()

    def add_cluster(self, cluster_id: str, name: str, child_ids: list[str]) -> dict:
        with self.session() as session:
            row = ClusterRow(
                id=cluster_id,
                name=name,
                status="Queued",
                child_ids_json=json.dumps(child_ids),
                created_at=utcnow(),
            )
            session.add(row)
            session.commit()
            return {"id": row.id, "name": row.name, "status": row.status, "child_ids": child_ids}

    def list_clusters(self) -> list[dict]:
        with self.session() as session:
            rows = session.scalars(select(ClusterRow)).all()
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "status": row.status,
                    "child_ids": _loads(row.child_ids_json, []),
                }
                for row in rows
            ]

    def save_cluster_status(self, cluster_id: str, status: str) -> None:
        with self.session() as session:
            row = session.get(ClusterRow, cluster_id)
            if row:
                row.status = status
                session.commit()

    def list_locks(self) -> list[LockRow]:
        with self.session() as session:
            return list(session.scalars(select(LockRow)).all())

    def get_lock(self, resource_type: str, resource_id: str) -> LockRow | None:
        with self.session() as session:
            return session.scalar(
                select(LockRow).where(LockRow.resource_type == resource_type, LockRow.resource_id == resource_id)
            )

    def insert_lock(self, resource_type: str, resource_id: str, holder: str, expires_at: datetime) -> bool:
        with self.session() as session:
            existing = session.scalar(
                select(LockRow).where(LockRow.resource_type == resource_type, LockRow.resource_id == resource_id)
            )
            if existing is not None:
                if ensure_naive(existing.expires_at) <= utcnow():
                    session.delete(existing)
                    session.flush()
                elif existing.holder == holder:
                    existing.expires_at = expires_at
                    session.commit()
                    return True
                else:
                    return False
            session.add(
                LockRow(
                    id=uuid.uuid4().hex,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    holder=holder,
                    expires_at=expires_at,
                )
            )
            session.commit()
            return True

    def delete_locks_for_holder(self, holder: str) -> None:
        with self.session() as session:
            rows = session.scalars(select(LockRow).where(LockRow.holder == holder)).all()
            for row in rows:
                session.delete(row)
            session.commit()

    def expire_locks(self, now: datetime | None = None) -> int:
        now = now or utcnow()
        with self.session() as session:
            rows = session.scalars(select(LockRow).where(LockRow.expires_at <= now)).all()
            count = len(rows)
            for row in rows:
                session.delete(row)
            session.commit()
            return count

    def insert_measurement(self, **fields) -> tuple[dict, bool]:
        with self.session() as session:
            existing = session.scalar(
                select(MeasurementRow).where(MeasurementRow.idempotency_key == fields["idempotency_key"])
            )
            if existing is not None:
                return self._measurement_dict(existing), True
            row = MeasurementRow(id=uuid.uuid4().hex, **fields)
            session.add(row)
            session.commit()
            return self._measurement_dict(row), False

    def list_measurements(
        self,
        *,
        task_id: str | None = None,
        point_id: str | None = None,
        metric: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[dict]:
        with self.session() as session:
            stmt = select(MeasurementRow).order_by(MeasurementRow.ts)
            if task_id:
                stmt = stmt.where(MeasurementRow.task_id == task_id)
            if point_id:
                stmt = stmt.where(MeasurementRow.point_id == point_id)
            if metric:
                stmt = stmt.where(MeasurementRow.metric == metric)
            if since:
                stmt = stmt.where(MeasurementRow.ts >= since)
            if until:
                stmt = stmt.where(MeasurementRow.ts <= until)
            return [self._measurement_dict(row) for row in session.scalars(stmt).all()]

    def add_alarm(self, **fields) -> dict:
        now = utcnow()
        with self.session() as session:
            row = AlarmRow(id=uuid.uuid4().hex, ts=now, updated_at=now, **fields)
            session.add(row)
            session.commit()
            return self._alarm_dict(row)

    def list_alarms(self, *, state: str | None = None, severity: str | None = None) -> list[dict]:
        with self.session() as session:
            stmt = select(AlarmRow).order_by(AlarmRow.ts.desc())
            if state:
                stmt = stmt.where(AlarmRow.state == state)
            if severity:
                stmt = stmt.where(AlarmRow.severity == severity)
            return [self._alarm_dict(row) for row in session.scalars(stmt).all()]

    def get_alarm(self, alarm_id: str) -> dict:
        with self.session() as session:
            row = session.get(AlarmRow, alarm_id)
            if row is None:
                raise not_found("报警不存在")
            return self._alarm_dict(row)

    def update_alarm(self, alarm_id: str, **fields) -> dict:
        with self.session() as session:
            row = session.get(AlarmRow, alarm_id)
            if row is None:
                raise not_found("报警不存在")
            for key, value in fields.items():
                setattr(row, key, value)
            row.updated_at = utcnow()
            session.commit()
            return self._alarm_dict(row)

    def append_audit(self, **fields) -> dict:
        with self.session() as session:
            row = AuditRow(id=uuid.uuid4().hex, ts=utcnow(), **fields)
            session.add(row)
            session.commit()
            return {
                "id": row.id,
                "actor": row.actor,
                "action": row.action,
                "object_ref": row.object_ref,
                "before": _loads(row.before_json, {}),
                "after": _loads(row.after_json, {}),
                "request_id": row.request_id,
                "ts": row.ts.isoformat(),
            }

    def list_audits(self) -> list[dict]:
        with self.session() as session:
            rows = session.scalars(select(AuditRow).order_by(AuditRow.ts)).all()
            return [
                {
                    "id": row.id,
                    "actor": row.actor,
                    "action": row.action,
                    "object_ref": row.object_ref,
                    "before": _loads(row.before_json, {}),
                    "after": _loads(row.after_json, {}),
                    "request_id": row.request_id,
                    "ts": row.ts.isoformat(),
                }
                for row in rows
            ]

    def add_approval(self, **fields) -> dict:
        now = utcnow()
        with self.session() as session:
            row = ApprovalRow(id=uuid.uuid4().hex, created_at=now, updated_at=now, **fields)
            session.add(row)
            session.commit()
            return self._approval_dict(row)

    def list_approvals(self, state: str | None = None) -> list[dict]:
        with self.session() as session:
            stmt = select(ApprovalRow).order_by(ApprovalRow.created_at.desc())
            if state:
                stmt = stmt.where(ApprovalRow.state == state)
            return [self._approval_dict(row) for row in session.scalars(stmt).all()]

    def get_approval(self, approval_id: str) -> dict:
        with self.session() as session:
            row = session.get(ApprovalRow, approval_id)
            if row is None:
                raise not_found("批准请求不存在")
            return self._approval_dict(row)

    def save_approval(self, approval: dict) -> dict:
        with self.session() as session:
            row = session.get(ApprovalRow, approval["id"])
            if row is None:
                raise not_found("批准请求不存在")
            row.state = approval["state"]
            row.approver = approval.get("approver")
            row.comment = approval.get("comment") or ""
            row.updated_at = utcnow()
            session.commit()
            return self._approval_dict(row)

    def add_esign(self, user_id: str, meaning: str, object_ref: str) -> None:
        with self.session() as session:
            session.add(
                ESignRow(
                    id=uuid.uuid4().hex,
                    user_id=user_id,
                    meaning=meaning,
                    object_ref=object_ref,
                    method="password",
                    ts=utcnow(),
                )
            )
            session.commit()

    def add_report(self, task_ref: str, file_uri: str, fmt: str, summary: dict) -> dict:
        with self.session() as session:
            row = ReportRow(
                id=uuid.uuid4().hex,
                task_ref=task_ref,
                file_uri=file_uri,
                format=fmt,
                summary_json=json.dumps(summary, ensure_ascii=False),
                generated_at=utcnow(),
            )
            session.add(row)
            session.commit()
            return self._report_dict(row)

    def list_reports(self) -> list[dict]:
        with self.session() as session:
            rows = session.scalars(select(ReportRow).order_by(ReportRow.generated_at.desc())).all()
            return [self._report_dict(row) for row in rows]

    def get_report(self, report_id: str) -> dict:
        with self.session() as session:
            row = session.get(ReportRow, report_id)
            if row is None:
                raise not_found("报告不存在")
            return self._report_dict(row)

    def add_backup(self, uri: str, scope: str) -> dict:
        with self.session() as session:
            row = BackupRow(id=uuid.uuid4().hex, uri=uri, scope=scope, created_at=utcnow())
            session.add(row)
            session.commit()
            return {"id": row.id, "uri": row.uri, "scope": row.scope, "created_at": row.created_at.isoformat()}

    def list_backups(self) -> list[dict]:
        with self.session() as session:
            rows = session.scalars(select(BackupRow).order_by(BackupRow.created_at.desc())).all()
            return [
                {"id": row.id, "uri": row.uri, "scope": row.scope, "created_at": row.created_at.isoformat()}
                for row in rows
            ]

    def get_backup(self, backup_id: str) -> dict:
        with self.session() as session:
            row = session.get(BackupRow, backup_id)
            if row is None:
                raise not_found("备份不存在")
            return {"id": row.id, "uri": row.uri, "scope": row.scope, "created_at": row.created_at.isoformat()}

    def create_group(self, name: str, user_ids: list[str], role_name: str = "") -> dict:
        with self.session() as session:
            if role_name and session.get(RoleRow, role_name) is None:
                raise not_found(f"角色 {role_name} 不存在")
            group = GroupRow(id=uuid.uuid4().hex, name=name, role_name=role_name)
            session.add(group)
            for user_id in user_ids:
                session.add(GroupMemberRow(group_id=group.id, user_id=user_id))
            session.commit()
            return {"id": group.id, "name": name, "role_name": role_name, "user_ids": user_ids}

    def ensure_group(self, name: str, role_name: str, user_ids: list[str]) -> dict:
        with self.session() as session:
            group = session.scalar(select(GroupRow).where(GroupRow.name == name))
            if group is None:
                group = GroupRow(id=uuid.uuid4().hex, name=name, role_name=role_name)
                session.add(group)
                session.flush()
            elif role_name and not group.role_name:
                group.role_name = role_name
            existing = set(session.scalars(select(GroupMemberRow.user_id).where(GroupMemberRow.group_id == group.id)).all())
            for user_id in user_ids:
                if user_id not in existing:
                    session.add(GroupMemberRow(group_id=group.id, user_id=user_id))
            session.commit()
            members = list(session.scalars(select(GroupMemberRow.user_id).where(GroupMemberRow.group_id == group.id)).all())
            return {"id": group.id, "name": group.name, "role_name": group.role_name, "user_ids": members}

    def update_group(self, group_id: str, role_name: str | None, user_ids: list[str] | None) -> dict:
        with self.session() as session:
            group = session.get(GroupRow, group_id)
            if group is None:
                raise not_found("用户组不存在")
            if role_name is not None:
                if role_name and session.get(RoleRow, role_name) is None:
                    raise not_found(f"角色 {role_name} 不存在")
                group.role_name = role_name
            if user_ids is not None:
                current = session.scalars(select(GroupMemberRow).where(GroupMemberRow.group_id == group.id)).all()
                for row in current:
                    session.delete(row)
                for user_id in user_ids:
                    session.add(GroupMemberRow(group_id=group.id, user_id=user_id))
            session.commit()
            members = list(session.scalars(select(GroupMemberRow.user_id).where(GroupMemberRow.group_id == group.id)).all())
            return {"id": group.id, "name": group.name, "role_name": group.role_name, "user_ids": members}

    def list_groups(self) -> list[dict]:
        with self.session() as session:
            groups = session.scalars(select(GroupRow)).all()
            result = []
            for group in groups:
                members = session.scalars(select(GroupMemberRow.user_id).where(GroupMemberRow.group_id == group.id)).all()
                result.append({"id": group.id, "name": group.name, "role_name": group.role_name or "", "user_ids": list(members)})
            return result

    def commit_decision(
        self,
        approval_id: str,
        state: str,
        approver: str,
        comment: str,
        user_id: str,
        meaning: str,
        object_ref: str,
        apply,
    ) -> dict:
        """批准状态、电子签名与领域变更同一事务提交。"""
        with self.session() as session:
            row = session.get(ApprovalRow, approval_id)
            if row is None:
                raise not_found("批准请求不存在")
            row.state = state
            row.approver = approver
            row.comment = comment or ""
            row.updated_at = utcnow()
            session.add(
                ESignRow(
                    id=uuid.uuid4().hex,
                    user_id=user_id,
                    meaning=meaning,
                    object_ref=object_ref,
                    method="password",
                    ts=utcnow(),
                )
            )
            if apply is not None:
                apply(session)
            session.commit()
            return self._approval_dict(row)

    @staticmethod
    def _user_dict(user: UserRow, roles: list[str]) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "disabled": bool(user.disabled),
            "roles": roles,
        }

    @staticmethod
    def _map_dict(row: MapRow) -> dict:
        return {
            "id": row.id,
            "name": row.name,
            "source": row.source,
            "width_m": row.width_m,
            "height_m": row.height_m,
            "meta": _loads(row.meta_json, {}),
        }

    @staticmethod
    def _point_dict(row: PointRow) -> dict:
        pose = _loads(row.pose_json, {})
        return {
            "id": row.id,
            "map_id": row.map_id,
            "name": row.name,
            "pose": pose,
            "instrument_profile": row.instrument_profile,
            "limits": _loads(row.limits_json, {}),
        }

    @staticmethod
    def _task_dict(row: TaskRow) -> dict:
        return {
            "id": row.id,
            "robot_id": row.robot_id,
            "status": row.status,
            "skills": _loads(row.skills_json, []),
            "skill_index": row.skill_index,
            "on_fail": row.on_fail,
            "error_code": row.error_code,
            "error_message": row.error_message,
            "client_request_id": row.client_request_id,
            "composite_id": row.composite_id,
            "cluster_id": row.cluster_id,
            "depends_on": row.depends_on,
            "timeline": _loads(row.timeline_json, []),
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    @staticmethod
    def _composite_dict(row: CompositeRow) -> dict:
        return {
            "id": row.id,
            "name": row.name,
            "status": row.status,
            "child_ids": _loads(row.child_ids_json, []),
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    def _measurement_dict(row: MeasurementRow) -> dict:
        return {
            "id": row.id,
            "idempotency_key": row.idempotency_key,
            "task_id": row.task_id,
            "point_id": row.point_id,
            "robot_id": row.robot_id,
            "device_id": row.device_id,
            "metric": row.metric,
            "value": row.value,
            "unit": row.unit,
            "quality": row.quality,
            "ts": row.ts.isoformat(),
        }

    @staticmethod
    def _alarm_dict(row: AlarmRow) -> dict:
        return {
            "id": row.id,
            "rule_id": row.rule_id,
            "severity": row.severity,
            "state": row.state,
            "source": row.source,
            "message": row.message,
            "object_ref": row.object_ref,
            "ack_by": row.ack_by,
            "note": row.note,
            "ts": row.ts.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    @staticmethod
    def _approval_dict(row: ApprovalRow) -> dict:
        return {
            "id": row.id,
            "object_ref": row.object_ref,
            "action": row.action,
            "payload": _loads(row.payload_json, {}),
            "state": row.state,
            "requester": row.requester,
            "approver": row.approver,
            "comment": row.comment,
            "expires_at": row.expires_at.isoformat(),
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }

    @staticmethod
    def _report_dict(row: ReportRow) -> dict:
        return {
            "id": row.id,
            "task_ref": row.task_ref,
            "file_uri": row.file_uri,
            "format": row.format,
            "summary": _loads(row.summary_json, {}),
            "generated_at": row.generated_at.isoformat(),
        }


def pose_from_dict(data: dict | None) -> Pose:
    data = data or {}
    return Pose(
        x=float(data.get("x", 0)),
        y=float(data.get("y", 0)),
        theta=float(data.get("theta", 0)),
        map_id=data.get("map_id"),
    )
