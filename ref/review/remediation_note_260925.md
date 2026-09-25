# Scheme / Plan 审核整改说明（2026-09-25）

| 项 | 内容 |
|----|------|
| 对象 | `ref/project_scheme.md` V0.4；`ref/plan.md` V0.4 |
| 依据 | `ref/review/review_project_scheme_260925.md`；`ref/review/review_plan_260925.md` |
| 作者 | PM_Max |

## project_scheme 已关闭

| 审核 ID | 级别 | 落点 |
|---------|------|------|
| SCH-001 | P0 | §9 按 plan §1.2 **逐字对齐** M0–M7 编号与名称 |
| SCH-002 | P0 | §4.4 `elevators[]`；§2/§4.3/§5 ElevatorAdapter |
| SCH-003 | P1 | §5.1 资源锁方案 + 2 机伪流程 |
| SCH-004 | P1 | §6.1 续传幂等与重试责任 |
| SCH-005 | P1 | §8.2 日志与健康检查 |
| SCH-006 | P1 | §4.3.1 Bearer/限流/权限映射/v2 |
| SCH-007 | P1 | §4.2 目录权威声明 |
| SCH-008 | P1 | §8.1 部署安全清单（内网 HTTP+强制鉴权） |
| SCH-009 | P2 | §6 导出 CSV；报告先 HTML |
| SCH-010 | P2 | §9 拆分后无合并表述 |
| SCH-011 | P2 | §3.3 Measurement quality |

## plan 已关闭

| 审核 ID | 级别 | 落点 |
|---------|------|------|
| PLN-001 | P0 | §1.2 权威声明；要求 scheme 对齐 |
| PLN-002 | P0 | TC-MVP-16..24；Should 书面豁免规则 |
| PLN-003 | P1 | §1.2 相对工期列 |
| PLN-004 | P1 | §8 维护 progress/tasks/risks |
| PLN-005 | P1 | P0a/P0b/P0c |
| PLN-006 | P1 | §6.4 DoD |
| PLN-007 | P1 | TC-MVP-13a/b/c |
| PLN-008 | P1 | §3.1 Vue 页面清单 |
| PLN-009 | P2 | §6.1 仿真 M2/M4 各一次 |
| PLN-010 | P2 | §7 文档漂移/TBD 风险 |
| PLN-011 | P2 | §2 `doc/test.md` |

## 三项 P0 交叉落点（供复审差分）

1. **里程碑权威**：plan §1.2（声明+表）→ scheme §9（逐字）→ DS 文首权威声明  
2. **ElevatorAdapter**：DS §4.1/§7/架构图 → scheme §2.1/§4.3/§4.4 elevators[]/§5 → plan Fake 要求与 TC-MVP-11  
3. **URS 追溯矩阵**：DS **附录 A**（45 Must 全覆盖）

## 建议

请 Reviewer_Max 复审 V0.4；确认 SCH-001 与 plan 表无漂移后可关 M0。
