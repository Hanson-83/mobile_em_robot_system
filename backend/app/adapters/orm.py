"""SQLite / PostgreSQL 共用表结构。开发与 CI 用 SQLite；生产用 PostgreSQL。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SchemaVersion(Base):
    __tablename__ = "schema_migrations"

    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    display_name: Mapped[str] = mapped_column(String(128), default="")
    disabled: Mapped[int] = mapped_column(Integer, default=0)


class RoleRow(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)


class UserRoleRow(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role_name: Mapped[str] = mapped_column(String(64), primary_key=True)


class RolePermissionRow(Base):
    __tablename__ = "role_permissions"

    role_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    permission: Mapped[str] = mapped_column(String(128), primary_key=True)


class GroupRow(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    role_name: Mapped[str] = mapped_column(String(64), default="")


class GroupMemberRow(Base):
    __tablename__ = "group_members"

    group_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)


class ApiTokenRow(Base):
    __tablename__ = "api_tokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    role_name: Mapped[str] = mapped_column(String(64))


class KvRow(Base):
    __tablename__ = "app_kv"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, default="{}")


class MapRow(Base):
    __tablename__ = "maps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(64), default="seed")
    width_m: Mapped[float] = mapped_column(Float, default=20.0)
    height_m: Mapped[float] = mapped_column(Float, default=15.0)
    meta_json: Mapped[str] = mapped_column(Text, default="{}")


class PointRow(Base):
    __tablename__ = "points"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    map_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))
    pose_json: Mapped[str] = mapped_column(Text, default="{}")
    instrument_profile: Mapped[str] = mapped_column(String(64), default="particle+climate+airflow")
    limits_json: Mapped[str] = mapped_column(Text, default="{}")


class TaskRow(Base):
    __tablename__ = "tasks"
    __table_args__ = (UniqueConstraint("client_request_id", name="uq_task_client_request"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    robot_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    skills_json: Mapped[str] = mapped_column(Text, default="[]")
    skill_index: Mapped[int] = mapped_column(Integer, default=0)
    on_fail: Mapped[str] = mapped_column(String(32), default="none")
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    composite_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    cluster_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    depends_on: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timeline_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CompositeRow(Base):
    __tablename__ = "composites"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), index=True)
    child_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ClusterRow(Base):
    __tablename__ = "clusters"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), index=True)
    child_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LockRow(Base):
    __tablename__ = "resource_locks"
    __table_args__ = (UniqueConstraint("resource_type", "resource_id", name="uq_resource_lock"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[str] = mapped_column(String(64))
    holder: Mapped[str] = mapped_column(String(64), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MeasurementRow(Base):
    __tablename__ = "measurements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    point_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    robot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(32), default="")
    quality: Mapped[str] = mapped_column(String(16), default="good")
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AlarmRow(Base):
    __tablename__ = "alarms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(128), default="")
    severity: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(16), index=True)
    source: Mapped[str] = mapped_column(String(64), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    object_ref: Mapped[str] = mapped_column(String(128), default="")
    ack_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditRow(Base):
    """只追加。仓储不提供 update/delete。"""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128))
    object_ref: Mapped[str] = mapped_column(String(128))
    before_json: Mapped[str] = mapped_column(Text, default="{}")
    after_json: Mapped[str] = mapped_column(Text, default="{}")
    request_id: Mapped[str] = mapped_column(String(64), default="-")
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ApprovalRow(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    object_ref: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    state: Mapped[str] = mapped_column(String(32), index=True)
    requester: Mapped[str] = mapped_column(String(64))
    approver: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ESignRow(Base):
    __tablename__ = "esign_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64))
    meaning: Mapped[str] = mapped_column(String(256))
    object_ref: Mapped[str] = mapped_column(String(128))
    method: Mapped[str] = mapped_column(String(64), default="password")
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReportRow(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_ref: Mapped[str] = mapped_column(String(64), index=True)
    file_uri: Mapped[str] = mapped_column(Text)
    format: Mapped[str] = mapped_column(String(16), default="html")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BackupRow(Base):
    __tablename__ = "backup_sets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    uri: Mapped[str] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(String(64), default="sqlite+config+reports")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
