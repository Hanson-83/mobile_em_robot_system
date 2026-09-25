# 测试与验证记录

| 项 | 内容 |
|----|------|
| 依据 | `ref/plan.md` §6；`spec/testing_quality.md` |
| 开始维护 | M1（2026-09-25） |
| 说明 | 真机/HIL 由用户执行并回填；软件侧 Fake 路径在 CI/本地执行 |

## 执行记录模板

| TC ID | URS ID | 层级 | 环境 | 日期 | 结果 | 执行者 | 备注 |
|-------|--------|------|------|------|------|--------|------|
| | | | | | 通过/失败/跳过/豁免 | | |

## M1 已执行（软件）

| TC ID | URS ID | 层级 | 环境 | 日期 | 结果 | 执行者 | 备注 |
|-------|--------|------|------|------|------|--------|------|
| TC-M1-SMOKE-ADAPTER | URS-ADP-001/003, URS-ROB-001 | 单元 | 本地 pytest | 2026-09-25 | 待测 | Dev_Max | Fake AMR/仪表 |
| TC-M1-SMOKE-ELEV | URS-ROB-007, URS-ADP-003 | 冒烟 | 本地 pytest | 2026-09-25 | 待测 | Dev_Max | ElevatorFake Call/Enter/Exit + 资源锁 |
| TC-M1-GW-OPENAPI | URS-API-001/002/004 | 集成 | TestClient | 2026-09-25 | 待测 | Dev_Max | 三分组 + 统一错误 |
| TC-M1-GW-AUTH | URS-SEC-001/003 | 集成 | TestClient | 2026-09-25 | 待测 | Dev_Max | 未鉴权 401；viewer 不可写任务 |
| TC-M1-IDEM | URS-DAT-005 | 集成 | TestClient | 2026-09-25 | 待测 | Dev_Max | 幂等键重复忽略 |
| TC-M1-ESIGN-DEFAULT | URS-AUD-004 | 集成 | TestClient | 2026-09-25 | 待测 | Dev_Max | 默认 e_sign=false |
| TC-MVP-01..24 | 见 plan §6.3 | — | — | — | 未开始 | — | M2–M4 |
| TC-HIL-* | 见 plan §6.3 | HIL | 用户现场 | — | 未开始 | 用户 | 不阻塞 Fake |

## 书面豁免

（空。Should 项豁免须写清 URS ID、理由、补测计划。）
