# 进度状态 — 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 更新日期 | 2026-09-26 |
| 当前阶段 | M0 文档基线已关闭；准备进入 M1（契约与骨架） |
| 状态 | Reviewer_Max 已确认 V0.4 三项 P0 通过，**可进入开发任务环境** |

## 已完成

- [x] URS/DS/方案/计划 V0.1 → V0.2（上位机范围）→ V0.2.1（Vue）→ V0.3（软件决策）→ V0.4（审核整改）
- [x] Reviewer_Max 三份审核（2026-09-25）
- [x] V0.4 审核整改（PM_Max）：电梯独立 ElevatorAdapter；里程碑以 plan §1.2 为准；DS 附录 A URS 追溯；P1/P2 补齐
- [x] Reviewer_Max V0.4 复审通过（2026-09-25）：plan/scheme M0–M7 对齐；ElevatorAdapter 统一；附录 A 覆盖 MVP Must
- [x] M0 文档基线正式关闭，获准进入开发

## 进行中

- （无）— 等待开工 M1

## 未开始（软件侧摘要）

- M1：仓库骨架（scheme §4.2）+ 契约冻结 + Fake 全链路（含 ElevatorFake）+ Gateway 草图（P0a）
- M2+：编排状态机、数据与合规、Vue MVP、Gateway 稳定、联调门禁等（见 `ref/plan.md`）
- 真机/用户 API 联调（并行门禁 M6，不阻塞 Fake）

## 跟踪文档

- `ref/tasks.md` — 任务板（精简）
- `ref/risks.md` — 风险板（精简）
- `doc/test.md` — 验收执行记录（M1 起维护）
- `doc/spec/review/remediation_note_260925.md` — V0.4 整改说明

## 后续行动

1. 按 plan 启动 M1：契约 + Fake + Gateway 草图（P0a）
2. 开发中顺手收口剩余 P1/P2（不另开文档大修）
3. 与用户硬件 Owner 对齐 API 文档节奏（不阻塞 Fake）
