"""限值变更与批准流。e_sign 关闭时直接生效；开启则生成待批请求。"""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.core.errors import DomainError
from app.core.security import Principal, verify_password
from app.services.store import Store

APPROVAL_TTL_S = 72 * 3600


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def audit(store: Store, enabled: bool, actor: str, action: str, obj: str, detail: dict[str, Any]) -> None:
    if not enabled:
        return
    store.append_audit(
        {
            "id": uuid4().hex[:12],
            "actor": actor,
            "action": action,
            "object": obj,
            "detail": detail,
            "ts": time.time(),
        }
    )


def sweep_expired(store: Store) -> None:
    now = time.time()
    for item in store.list_approvals():
        if item.get("state") == "Pending" and float(item.get("expires_at") or 0) < now:
            item["state"] = "Expired"
            store.save_approval(item)


def request_limit_change(
    *,
    store: Store,
    limits: dict[str, Any],
    patch: dict[str, Any],
    actor: Principal,
    e_sign: bool,
    audit_on: bool,
) -> dict[str, Any]:
    if not patch:
        raise DomainError("VALIDATION_ERROR", "限值变更不能为空")
    if not e_sign:
        merged = deep_merge(limits, patch)
        limits.clear()
        limits.update(merged)
        audit(store, audit_on, actor.username, "limit.update", "limits", {"patch": patch})
        return {"applied": True, "limits": limits}
    approval = {
        "id": uuid4().hex[:12],
        "state": "Pending",
        "action": "limit.update",
        "object_ref": "limits",
        "payload": patch,
        "requester": actor.username,
        "expires_at": time.time() + APPROVAL_TTL_S,
        "meaning": "限值变更",
    }
    store.save_approval(approval)
    audit(store, audit_on, actor.username, "approval.create", approval["id"], {"action": "limit.update"})
    raise DomainError(
        "APPROVAL_REQUIRED",
        "签名已开启，限值变更须批准后生效",
        details={"approval_id": approval["id"]},
    )


def decide_approval(
    *,
    store: Store,
    limits: dict[str, Any],
    approval_id: str,
    decision: str,
    actor: Principal,
    password: str,
    meaning: str,
    audit_on: bool,
) -> dict[str, Any]:
    sweep_expired(store)
    item = store.get_approval(approval_id)
    if not item:
        raise DomainError("NOT_FOUND", f"批准请求 {approval_id} 不存在")
    if item["state"] == "Expired" or (
        item["state"] == "Pending" and float(item["expires_at"]) < time.time()
    ):
        item["state"] = "Expired"
        store.save_approval(item)
        raise DomainError("APPROVAL_REJECTED", "批准请求已过期")
    if item["state"] != "Pending":
        raise DomainError("VALIDATION_ERROR", f"当前状态 {item['state']} 不可审批")
    if actor.username == item["requester"]:
        raise DomainError("FORBIDDEN", "审批人不能是发起人")
    if not verify_password(actor.username, password):
        raise DomainError("AUTH_REQUIRED", "签名口令错误")
    if decision not in {"approved", "rejected"}:
        raise DomainError("VALIDATION_ERROR", "decision 须为 approved 或 rejected")
    item["approver"] = actor.username
    item["meaning"] = meaning or item.get("meaning")
    item["signed_at"] = time.time()
    if decision == "rejected":
        item["state"] = "Rejected"
        store.save_approval(item)
        audit(store, audit_on, actor.username, "approval.reject", approval_id, {})
        return item
    item["state"] = "Approved"
    if item.get("action") == "limit.update":
        merged = deep_merge(limits, item.get("payload") or {})
        limits.clear()
        limits.update(merged)
    store.save_approval(item)
    audit(store, audit_on, actor.username, "approval.approve", approval_id, {"meaning": item["meaning"]})
    return item
