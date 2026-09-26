"""Modbus 保持寄存器模拟。

厂商寄存器表未提供。此处按常规占位：
- 粒子 unit 1：地址 0..3 依次为 0.1 / 0.5 / 1.0 / 5.0 µm 计数（整数）
- 温湿度 unit 2：地址 0 温度×10（℃），地址 1 湿度×10（%）
- 风速 unit 3：地址 0 风速×100（m/s）

真机替换为实际 Modbus TCP/RTU 客户端时，只换传输层，不改编排。
"""

from __future__ import annotations


class ModbusHoldingSim:
    def __init__(self, unit_id: int) -> None:
        self.unit_id = unit_id
        self._regs: dict[int, int] = {}

    def write_registers(self, address: int, values: list[int]) -> None:
        for i, v in enumerate(values):
            self._regs[address + i] = int(v) & 0xFFFF

    def read_holding(self, address: int, count: int) -> list[int]:
        return [self._regs.get(address + i, 0) for i in range(count)]
