from __future__ import annotations

import pytest

from app.adapters.factory import AdapterFactory
from app.core.config import load_devices, resolve_config_dir
from app.core.errors import DomainError


def test_factory_loads_example_yaml() -> None:
    cfg = load_devices(resolve_config_dir())
    assert cfg.elevators[0].id == "elev-01"
    assert cfg.instruments[0].access_mode == "direct"
    reg = AdapterFactory.build(cfg)
    assert set(reg.robots) == {"robot-01"}
    assert "elev-01" in reg.elevators
    assert "pc-01" in reg.instruments


def test_factory_rejects_edge_agent_in_mvp() -> None:
    cfg = load_devices(resolve_config_dir())
    cfg.instruments[0].access_mode = "via_edge_agent"
    with pytest.raises(DomainError) as ei:
        AdapterFactory.build(cfg)
    assert ei.value.code == "VALIDATION_ERROR"
