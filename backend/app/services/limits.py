"""点位/指标限值。签名关闭时直接读配置；批准流属 M3。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_limits(config_dir: Path) -> dict[str, Any]:
    path = config_dir / "limits.example.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def particle_exceeds(channel: str, value: float, limits: dict[str, Any]) -> bool:
    table = limits.get("particle") or {}
    rule = table.get(channel) or {}
    max_v = rule.get("max")
    return max_v is not None and value > float(max_v)


def scalar_exceeds(metric: str, value: float, limits: dict[str, Any]) -> bool:
    rule = limits.get(metric) or {}
    max_v = rule.get("max")
    return max_v is not None and value > float(max_v)
