"""厂商适配占位：待用户提供 API 文档后实现。切换 YAML adapter 即可，不改编排。"""

from __future__ import annotations

from typing import Any

from app.core.errors import DomainError


class VendorStub:
    def __init__(self, device_id: str, vendor: str, **_k: Any) -> None:
        self.device_id = device_id
        self.vendor = vendor

    def connect(self) -> None:
        raise DomainError(
            "NOT_IMPLEMENTED",
            f"{self.vendor} 适配器待用户 API 文档后实现（device={self.device_id}）",
        )

    def disconnect(self) -> None:
        return None

    def health(self) -> dict[str, Any]:
        return {"id": self.device_id, "type": self.vendor, "online": False, "stub": True}

    def __getattr__(self, name: str) -> Any:
        def _missing(*_a: Any, **_k: Any) -> Any:
            raise DomainError(
                "NOT_IMPLEMENTED",
                f"{self.vendor}.{name} 未实现，等待真机契约",
            )

        return _missing


class AmrVendorX(VendorStub):
    def __init__(self, device_id: str, **kw: Any) -> None:
        super().__init__(device_id, vendor="amr_vendor_x", **kw)


class ElevatorVendorX(VendorStub):
    def __init__(self, device_id: str, **kw: Any) -> None:
        super().__init__(device_id, vendor="elevator_vendor_x", **kw)


class ParticleVendorX(VendorStub):
    def __init__(self, device_id: str, **kw: Any) -> None:
        super().__init__(device_id, vendor="particle_vendor_x", **kw)
