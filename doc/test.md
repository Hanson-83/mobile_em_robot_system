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
| M2 | 2026-09-26 | 状态机、排队、重连、报警、报告见 §3；HIL 跳过 |

## 2. 用例登记（plan §6.3）

| 用例 | URS | 层级 | 本轮结果 | 证据 | 豁免 |
|------|-----|------|----------|------|------|
| TC-MVP-02 Fake 任务全流程（含电梯） | URS-SCH-001/002, URS-DAT-001 | E2E/冒烟 | **通过（Fake）** | `test_smoke_task.py` + 状态机 | |
| TC-MVP-03 超限报警并可确认 | URS-ALM-001/002 | E2E | **通过（Fake）** | `test_m2_scheduler.py` | |
| TC-MVP-04 任务批报告 HTML | URS-RPT-001 | E2E | **通过** | `POST /api/v1/reports` | PDF 未做 |
| TC-MVP-08 部分（鉴权/OpenAPI/错误体） | URS-API-001/002/004, URS-SEC-003 | 集成 | **通过（草图）** | `test_gateway.py` `test_error_body.py` | 稳定版待 M5 |
| TC-MVP-10 部分（Fake 装配） | URS-ADP-001/003/004 | 集成 | **通过** | `backend/tests/test_factory.py` | 真机适配器占位 |
| TC-MVP-11 电梯 Fake Call/Enter/Exit | URS-ROB-007 | E2E | **通过（Fake）** | 冒烟门状态 | 真机 HIL 用户执行 |
| TC-MVP-12 简单互斥 | URS-SCH-003 | 集成 | **通过** | queue 排队 + fail 单测 | |
| TC-MVP-13a 部分（默认 e_sign=false） | URS-AUD-004 | 集成 | **通过** | `/ready` 断言 `e_sign=false` | 批准流待 M3 |
| TC-MVP-16 部分 GeoJSON 点位 | URS-SCH-004 | 集成 | **通过（占位）** | `POST /maps/import` | ROS 地图未解析 |
| TC-MVP-18 断线重连 | URS-ROB-005 | 集成 | **通过（Fake）** | 瞬断成功；持续断链失败 | |
| TC-MVP-19 急停导致任务失败 | URS-ROB-009 | 集成 | **通过（Fake）** | 任务 Failed / DEVICE_ESTOP | |
| TC-MVP-23 进程中断 | URS-NFR-002 | 集成 | **通过** | Running → PROCESS_LOST | |
| 其余 TC-MVP-* | — | — | **未测** | — | 按里程碑展开 |
| TC-HIL-* | — | HIL | **跳过** | — | 用户真机环境 |

Should 项书面豁免：本轮无。

## 3. M1 自动化

命令：`cd backend && pytest`（venv）。M2 当轮 **30 passed**。

## 4. 真机回填区（用户）

| 日期 | 环境 | 设备 | 结果 | 备注 |
|------|------|------|------|------|
| | | | | |
