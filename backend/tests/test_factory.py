from __future__ import annotations

import pytest

from app.adapters.factory import AdapterFactory
from app.adapters.placeholders import ArmAdapterPlaceholder, ViableAdapterPlaceholder
from app.core.config import DevicesFile, InstrumentConfig, RobotConfig, load_devices, load_features
from app.core.errors import DomainError


def test_factory_from_example_yaml(settings):
    devices = load_devices(settings.repo_root / "config/devices.example.yaml")
    features = load_features(settings.repo_root / "config/features.example.yaml")
    registry = AdapterFactory.build(devices)
    assert "robot-01" in registry.robots
    assert "elev-01" in registry.elevators
    assert {"pc-01", "th-01", "af-01"} <= set(registry.instruments)
    assert features.e_sign is False
    assert features.realtime_channel == "websocket"
    assert all(i.access_mode == "direct" for i in devices.instruments)


def test_factory_rejects_vendor_placeholder():
    devices = DevicesFile(robots=[RobotConfig(id="r1", adapter="amr_vendor_x")])
    with pytest.raises(DomainError) as exc:
        AdapterFactory.build(devices)
    assert "占位" in exc.value.message


def test_factory_rejects_edge_agent():
    devices = DevicesFile(
        instruments=[
            InstrumentConfig(id="x", adapter="particle_fake", access_mode="via_edge_agent")
        ]
    )
    with pytest.raises(DomainError):
        AdapterFactory.build(devices)


def test_extension_placeholders_are_explicit():
    with pytest.raises(NotImplementedError):
        ViableAdapterPlaceholder()
    with pytest.raises(NotImplementedError):
        ArmAdapterPlaceholder()
