from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

import app.main_state as state
from app.api.deps import require
from app.core.errors import DomainError
from app.core.security import Principal, _dev_users
from app.services.backup import create_backup, restore_backup
from app.services.compliance import audit, decide_approval, request_limit_change, sweep_expired

router = APIRouter()


def _store():
    assert state.store is not None
    return state.store


@router.get("/api/v1/points", tags=["settings"])
def list_points(_user: Annotated[Principal, Depends(require("settings.point.read"))]) -> list[dict[str, Any]]:
    return _store().list_points()


@router.post("/api/v1/points", tags=["settings"])
def create_point(
    body: dict[str, Any],
    user: Annotated[Principal, Depends(require("settings.point.write"))],
) -> dict[str, Any]:
    if not body.get("id"):
        raise DomainError("VALIDATION_ERROR", "点位缺少 id")
    point = {
        "id": body["id"],
        "name": body.get("name") or body["id"],
        "map_id": body.get("map_id"),
        "pose": body.get("pose") or {},
        "limits": body.get("limits") or {},
    }
    _store().save_point(point)
    audit(_store(), state.features.audit_trail, user.username, "point.create", point["id"], {})
    return point


@router.patch("/api/v1/points/{point_id}", tags=["settings"])
def patch_point(
    point_id: str,
    body: dict[str, Any],
    user: Annotated[Principal, Depends(require("settings.point.write"))],
) -> dict[str, Any]:
    point = _store().get_point(point_id)
    if not point:
        raise DomainError("NOT_FOUND", f"点位 {point_id} 不存在")
    point.update({k: v for k, v in body.items() if k != "id"})
    _store().save_point(point)
    audit(_store(), state.features.audit_trail, user.username, "point.update", point_id, {})
    return point


@router.delete("/api/v1/points/{point_id}", tags=["settings"])
def delete_point(
    point_id: str,
    user: Annotated[Principal, Depends(require("settings.point.write"))],
) -> dict[str, Any]:
    if not _store().delete_point(point_id):
        raise DomainError("NOT_FOUND", f"点位 {point_id} 不存在")
    audit(_store(), state.features.audit_trail, user.username, "point.delete", point_id, {})
    return {"id": point_id, "deleted": True}


@router.get("/api/v1/settings/limits", tags=["settings"])
def get_limits(_user: Annotated[Principal, Depends(require("settings.limit.read"))]) -> dict[str, Any]:
    return {"e_sign": state.features.e_sign, "limits": state.limits}


@router.patch("/api/v1/settings/limits", tags=["settings"])
def patch_limits(
    body: dict[str, Any],
    user: Annotated[Principal, Depends(require("settings.limit.write"))],
) -> dict[str, Any]:
    return request_limit_change(
        store=_store(),
        limits=state.limits,
        patch=body,
        actor=user,
        e_sign=bool(state.features.e_sign),
        audit_on=bool(state.features.audit_trail),
    )


@router.patch("/api/v1/settings/features", tags=["settings"])
def patch_features(
    body: dict[str, Any],
    user: Annotated[Principal, Depends(require("settings.limit.write"))],
) -> dict[str, Any]:
    for key in ("audit_trail", "e_sign"):
        if key in body:
            setattr(state.features, key, bool(body[key]))
    audit(_store(), True, user.username, "features.update", "features", body)
    return state.features.model_dump()


@router.get("/api/v1/approvals", tags=["operations"])
def list_approvals(
    _user: Annotated[Principal, Depends(require("operations.approval.read"))],
) -> list[dict[str, Any]]:
    sweep_expired(_store())
    return _store().list_approvals()


@router.post("/api/v1/approvals/{approval_id}/decide", tags=["operations"])
def decide(
    approval_id: str,
    body: dict[str, Any],
    user: Annotated[Principal, Depends(require("operations.approval.write"))],
) -> dict[str, Any]:
    return decide_approval(
        store=_store(),
        limits=state.limits,
        approval_id=approval_id,
        decision=str(body.get("decision") or ""),
        actor=user,
        password=str(body.get("password") or ""),
        meaning=str(body.get("meaning") or ""),
        audit_on=bool(state.features.audit_trail),
    )


@router.get("/api/v1/audit", tags=["data"])
def list_audit(_user: Annotated[Principal, Depends(require("data.audit.read"))]) -> list[dict[str, Any]]:
    return _store().list_audit()


@router.delete("/api/v1/audit/{event_id}", tags=["data"])
def delete_audit(
    event_id: str,
    _user: Annotated[Principal, Depends(require("data.audit.read"))],
) -> None:
    raise DomainError("FORBIDDEN", f"审计记录只追加，禁止删除 {event_id}")


@router.get("/api/v1/trends", tags=["data"])
def trends(
    metric: str,
    _user: Annotated[Principal, Depends(require("data.measurement.read"))],
) -> dict[str, Any]:
    series = [row for row in _store().list_measurements() if row.get("metric") == metric]
    return {"metric": metric, "series": series}


@router.get("/api/v1/users", tags=["settings"])
def list_users(_user: Annotated[Principal, Depends(require("settings.user.read"))]) -> list[dict[str, Any]]:
    return [
        {"username": name, "roles": info.get("roles", [])}
        for name, info in _dev_users().items()
    ]


@router.post("/api/v1/users", tags=["settings"])
def create_user(_user: Annotated[Principal, Depends(require("settings.user.write"))]) -> dict[str, str]:
    raise DomainError("NOT_IMPLEMENTED", "用户目录由环境变量 MER_DEV_USERS_JSON 注入")


@router.post("/api/v1/admin/backup", tags=["settings"])
def backup(_user: Annotated[Principal, Depends(require("settings.backup.write"))]) -> dict[str, Any]:
    assert state.config_dir is not None and state.backup_dir is not None
    return create_backup(
        store=_store(),
        config_dir=state.config_dir,
        report_dir=state.report_dir,
        backup_root=state.backup_dir,
    )


@router.post("/api/v1/admin/restore", tags=["settings"])
def restore(
    body: dict[str, Any],
    user: Annotated[Principal, Depends(require("settings.backup.write"))],
) -> dict[str, Any]:
    assert state.config_dir is not None and state.backup_dir is not None
    result = restore_backup(
        store=_store(),
        config_dir=state.config_dir,
        report_dir=state.report_dir,
        backup_root=state.backup_dir,
        backup_id=str(body.get("id") or ""),
    )
    audit(_store(), state.features.audit_trail, user.username, "backup.restore", result["id"], {})
    return result
