"""录制回放适配器。用于在没有厂商 API 时跑通契约路径。"""

from __future__ import annotations

import json
from pathlib import Path

from app.adapters.fake_amr import AmrFake
from app.domain.dto import Pose


class AmrRecorded(AmrFake):
    """读取 JSON 剧本覆盖初始状态，其余行为与 Fake 相同（同一 AmrAdapter 契约）。"""

    def __init__(self, device_id: str, recording_path: str) -> None:
        super().__init__(device_id, adapter_type="amr_recorded")
        payload = json.loads(Path(recording_path).read_text(encoding="utf-8"))
        status = payload.get("status") or {}
        pose = status.get("pose") or {}
        self.pose = Pose(
            float(pose.get("x", 0)),
            float(pose.get("y", 0)),
            float(pose.get("theta", 0)),
            pose.get("map_id"),
        )
        self.battery_pct = float(status.get("battery_pct", self.battery_pct))
        self.estop = bool(status.get("estop", False))
        self.recording = payload
