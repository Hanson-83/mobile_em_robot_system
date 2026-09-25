"""适配器公共生命周期与错误。"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.core.errors import DomainError


class AdapterError(DomainError):
    """适配层错误，已映射为领域错误码。"""


@runtime_checkable
class Lifecycle(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def health(self) -> dict[str, Any]: ...
