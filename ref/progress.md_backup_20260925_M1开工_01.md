# 进度状态 — 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 更新日期 | 2026-09-25 |
| 当前阶段 | 文档基线（M0）— V0.4 审核整改 |
| 状态 | DS / project_scheme / plan 已升 V0.4，待 Reviewer_Max 复审 |

## 已完成

- [x] URS/DS/方案/计划 V0.1 → V0.2（上位机范围）→ V0.2.1（Vue）→ V0.3（软件决策）
- [x] Reviewer_Max 三份审核（2026-09-25）
- [x] **V0.4 审核整改**（PM_Max）：电梯独立 ElevatorAdapter；里程碑以 plan §1.2 为准；DS 附录 A URS 追溯；P1/P2 补齐

## 进行中

- [ ] Reviewer_Max 对 V0.4 复审（差分关注：里程碑对齐、ElevatorAdapter、附录 A）
- [ ] M0 文档基线正式通过后进入 M1

## 未开始（软件侧摘要）

- 仓库骨架（scheme §4.2）+ Fake 全链路（含 ElevatorFake）
- OpenAPI 草图、适配接口冻结、编排状态机
- Vue MVP 页面（见 plan §3.1）
- 真机/用户 API 联调（并行门禁 M6）

## 跟踪文档

- `ref/tasks.md` — 任务板（精简）
- `ref/risks.md` — 风险板（精简）
- `doc/test.md` — 验收执行记录（M1 起维护）

## 后续行动

1. Reviewer_Max 复审关闭 DS/SCH/PLN 审核项  
2. M1：契约 + Fake + Gateway 草图（P0a）  
3. 与用户硬件 Owner 对齐 API 文档节奏（不阻塞 Fake）
