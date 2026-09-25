"""扩展/远期适配器占位（浮游菌、臂、深度相机）。不阻塞 MVP。"""

from __future__ import annotations

from typing import Any


class ViableAdapterPlaceholder:
    """URS-INS-006 扩展：浮游菌。"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("ViableAdapter 为扩展阶段占位，待用户提供浮游菌设备 API")


class ArmAdapterPlaceholder:
    """URS-ROB-011 远期：协作臂。"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("ArmAdapter 为远期占位，待用户提供臂 API")


class DepthCameraAdapterPlaceholder:
    """URS-ROB-011 远期：深度相机。"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("DepthCameraAdapter 为远期占位")
