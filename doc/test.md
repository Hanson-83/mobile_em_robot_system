# 验收执行记录（test.md）

| 项 | 内容 |
|----|------|
| 文档 | MER-TEST-001 |
| 创建 | 2026-09-25 |
| 维护 | 测试/验证；每个用例追溯 URS ID（PLN-011） |
| 说明 | HIL/真机由用户在专门环境执行后回填本表 |

## 1. 执行摘要

| 里程碑 | 窗口 | 结果 |
|--------|------|------|
| M1 | 2026-09-25 | Fake 单元/集成/冒烟见 §3；HIL 跳过 |

## 2. 用例登记（plan §6.3）

| 用例 | URS | 层级 | 本轮结果 | 证据 | 豁免 |
|------|-----|------|----------|------|------|
| TC-MVP-02 部分（Fake 任务冒烟） | URS-SCH-001/002, URS-DAT-001 | E2E/冒烟 | **通过（Fake）** | `backend/tests/test_smoke_task.py` | 完整状态机待 M2 |
| TC-MVP-08 部分（鉴权/OpenAPI 分组） | URS-API-001/002/004, URS-SEC-003 | 集成 | **通过（草图）** | `backend/tests/test_gateway.py` | 稳定版待 M5 |
| TC-MVP-10 部分（Fake 装配） | URS-ADP-001/003/004 | 集成 | **通过** | `backend/tests/test_factory.py` | 真机适配器占位 |
| TC-MVP-11 部分（电梯 Fake Call/Enter/Exit） | URS-ROB-007 | 单元+冒烟 | **通过（Fake）** | `test_adapters_fake.py` / smoke | 真机 HIL 用户执行 |
| TC-MVP-12 部分（点位互斥 fail） | URS-SCH-003 | 单元 | **通过（fail 策略）** | `backend/tests/test_mutex.py` | queue 排队待 M2 |
| TC-MVP-13a 部分（默认 e_sign=false） | URS-AUD-004 | 集成 | **通过** | `/ready` 断言 `e_sign=false` | 批准流待 M3 |
| TC-MVP-19 部分（急停注入拒发） | URS-ROB-009 | 单元 | **通过（Fake）** | `AmrFake.inject(estop=True)` | 调度中断任务待 M2 |
| 其余 TC-MVP-* | — | — | **未测** | — | 按里程碑展开 |
| TC-HIL-* | — | HIL | **跳过** | — | 用户真机环境 |

Should 项书面豁免：本轮无。

## 3. M1 自动化

命令：`cd backend && pytest`（venv）。

失败项：无（以当轮 CI/本地输出为准）。

## 4. 真机回填区（用户）

| 日期 | 环境 | 设备 | 结果 | 备注 |
|------|------|------|------|------|
| | | | | |
