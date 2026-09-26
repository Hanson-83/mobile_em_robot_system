"""实时快照构建（Web / MES / WS 共用）。"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import app.main_state as state


def build_realtime_snapshot() -> dict[str, Any]:
    assert state.store is not None
    alarms = [a for a in state.store.list_alarms() if a.get("state") == "active"]
    robots: list[dict[str, Any]] = []
    if state.registry:
        for rid, amr in state.registry.robots.items():
            robots.append({"id": rid, "status": asdict(amr.get_status())})
    return {
        "robots": robots,
        "alarms": alarms,
        "measurements": state.store.list_measurements(),
        "tasks": [
            {"id": t["id"], "state": t["state"], "robot_id": t.get("robot_id")}
            for t in state.store.list_tasks()
        ],
    }
