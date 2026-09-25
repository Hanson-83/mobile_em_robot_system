# 项目规划（plan）V0.4 差分复审意见（2026-09-25）

## 1. 审核元信息

- 审核对象：`ref/plan.md` V0.4 / MER-PLAN-001
- 审核类型：整改后差分复审（对照 `ref/review/review_plan_260925.md` 与 `ref/review/remediation_note_260925.md`）
- 审核依据：`AGENTS.md`、`ref/requirement.md`、`doc/spec/urs.md` V0.3、`doc/spec/ds.md` V0.4、`ref/project_scheme.md` V0.4；`spec/testing_quality.md`
- 审核人：Reviewer_Max
- 审核日期：2026-09-25
- 总体结论：**有条件通过** — P0（PLN-001/002）与整改清单所列 P1 均已落实；`doc/test.md` 尚未创建（已规划 M1/T-010）、性能基线（URS-NFR-001）仍无独立 TC，属 P2 残留，**不阻塞 M0 收口与 M1 启动**。

## 2. 差分复审说明

| 审核 ID | 级别 | 复审结论 | 验证要点（V0.4 落点） |
|---------|------|----------|------------------------|
| PLN-001 | P0 | **已关闭** | §1.2 权威声明 + M0–M7 表；要求 scheme §9 逐字对齐 |
| PLN-002 | P0 | **已关闭** | TC-MVP-16..24 补齐地图/趋势/断线/急停/导出/审计只追加/Vue E2E/进程恢复/组合报告；§1.2 Should 书面豁免规则 |
| PLN-003 | P1 | **已关闭** | §1.2「相对工期（人周，估）」列 + T0/M6 说明 |
| PLN-004 | P1 | **已关闭** | §8 维护 `progress.md`/`tasks.md`/`risks.md`；工作区三文件已存在且与 M0 状态一致 |
| PLN-005 | P1 | **已关闭** | §4 P0a/P0b/P0c 拆分 |
| PLN-006 | P1 | **已关闭** | §6.4 DoD（lint/typecheck、单测、OpenAPI/schema、无密钥 diff） |
| PLN-007 | P1 | **已关闭** | TC-MVP-13a/b/c 拆分 + 默认 `e_sign=false` |
| PLN-008 | P1 | **已关闭** | §3.1 Vue MVP 页面清单（10 页 + URS 映射） |
| PLN-009 | P2 | **已关闭** | §6.1 仿真 M2/M4 各至少一次 |
| PLN-010 | P2 | **已关闭** | §7 文档漂移 / TBD 永久化风险 |
| PLN-011 | P2 | **部分** | §2/§6 已约定 `doc/test.md` 路径与 URS 追溯；**文件尚未创建**（`ref/tasks.md` T-010 规划 M1） |

**里程碑与 scheme 逐字对齐（PLN-001 交叉验证）**

| ID | plan §1.2 里程碑 | scheme §9 里程碑 | 对齐 |
|----|------------------|------------------|------|
| M0 | 文档基线 | 文档基线 | ✓ |
| M1 | 契约与骨架 | 契约与骨架 | ✓ |
| M2 | 调度 MVP | 调度 MVP | ✓ |
| M3 | 数据与合规 | 数据与合规 | ✓ |
| M4 | Web MVP 冻结 | Web MVP 冻结 | ✓ |
| M5 | Gateway 与多端契约 | Gateway 与多端契约 | ✓ |
| M6 | 联调门禁 | 联调门禁 | ✓ |
| M7 | 扩展 / 远期 | 扩展 / 远期 | ✓ |

scheme §9 第三列「软件交付物」为补充说明，未改写里程碑名称 — 符合权威声明。

**ElevatorAdapter 与测试**

- WBS-2/3、§6.3 TC-MVP-11 明确 **ElevatorAdapter** + Fake 不可豁免 — 与 DS/scheme V0.4 一致。

## 3. 符合项

- 唯一里程碑权威源表述清晰，且与 scheme §9、DS 文首声明三角一致。
- TC 矩阵从 TC-MVP-01 至 24 + HIL/EXT，覆盖 V0.3 审核 §5 所列 Must 缺口（地图、趋势、断线、急停、导出、CLI E2E 等）。
- Fake 主路径 + M6 并行门禁、电梯真机可豁免但 Fake 不可豁免 — 与 URS-NFR-006/ROB-007 一致。
- 跟踪文档已初始化：`ref/progress.md` 标明 M0 待复审；`ref/tasks.md`/`ref/risks.md` 承接 plan §7/§8。

## 4. 问题清单（残留）

| ID | 严重级别 | 位置 | 问题描述 | 建议 |
|----|----------|------|----------|------|
| PLN-R01 | P2 | `doc/test.md` | PLN-011 路径已写入 plan，但仓库尚无该文件 | M1 首周完成 T-010：模板 + 首条 M1 冒烟记录 |
| PLN-R02 | P2 | §6.3 | **URS-NFR-001** 无 TC；DS 附录脚注指向 M4 前 P95 基线 | M4 门禁前增加 TC 或 `doc/test.md` 性能记录节 |
| PLN-R03 | P2 | §6.3 | **URS-SEC-002**（Should）仍无专项 TC | M3 RBAC/安全配置阶段补集成用例或书面豁免 |
| PLN-R04 | P2 | 文档头 | `状态: Draft` — M0 通过后建议更新为 Baseline | PM 在 M0 纪要中冻结版本 |

**无未关闭 P0；无未关闭上一轮关键 P1。**

## 5. 需求追溯（Must 门禁可核对性）

- V0.3 缺口表（SCH-004/005、DAT-002、ROB-005/009、ALM-003、AUD-003、CLI-001、NFR-002）在 V0.4 均有 TC 映射。
- Should 项（RPT-002/003、AUD-003/004、ALM-002）在 TC 或 §1.2 书面豁免规则中有出口 — 可接受。

## 6. 与其他文档一致性

- 与 `project_scheme.md` V0.4：里程碑、ElevatorAdapter、`elevators[]`、目录权威 — 一致。
- 与 `ds.md` V0.4：批准流、API 资源表、备份范围、附录 A — plan TC 可回溯。
- `progress.md` 仍写「待 Reviewer_Max 复审」— 本复审完成后应由 PM 勾选 M0 项。

## 7. 结论与建议

- **总体结论：有条件通过**（条件：M1 启动同时完成 `doc/test.md` 初始化；其余为 P2 跟踪项）。
- **建议结束 M0、进入 M1**：契约与骨架（P0a）可按 §8 立即行动项执行。

## 8. 后续验证关注点

- M1 结束：核对 scheme §9 与 plan §1.2 未漂移（PLN-010 缓解措施）。
- M4 前：TC-MVP-16..24 不得长期 skip；Should 豁免须落 `doc/test.md`。
- CI 门禁与 §6.4 DoD 在首次 PR 即启用。
