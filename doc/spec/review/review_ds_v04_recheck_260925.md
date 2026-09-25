# 设计规范（DS）V0.4 差分复审意见（2026-09-25）

## 1. 审核元信息

- 审核对象：`doc/spec/ds.md` V0.4 / MER-DS-001
- 审核类型：整改后差分复审（对照 `doc/spec/review/review_ds_260925.md` 与 `doc/spec/review/remediation_note_260925.md`）
- 审核依据：`AGENTS.md`、`doc/spec/urs.md` V0.3、`ref/requirement.md`；`ref/plan.md` V0.4、`ref/project_scheme.md` V0.4；`spec/engineering_spec.md`、`interface_contracts.md`、`observability.md` 等
- 审核人：Reviewer_Max
- 审核日期：2026-09-25
- 总体结论：**通过** — 上一轮 P0（DS-001/002）与所列 P1/P2 整改项已在 V0.4 落盘且与 plan/scheme 交叉一致；附录 A 覆盖 MVP Must 45 条；残留「部分/TBD」已显式标注且不阻塞 M0 文档基线与 M1 契约开工。

## 2. 差分复审说明

| 审核 ID | 级别 | 复审结论 | 验证要点（V0.4 落点） |
|---------|------|----------|------------------------|
| DS-001 | P0 | **已关闭** | §1/§2/§3/§4.1：`ElevatorAdapter` 独立；`AmrAdapter` 仅导航/充电/遥测/急停，**不含** call/enter/exit_elevator；§7 Factory；架构图边 `ElevatorAdapter skills` |
| DS-002 | P0 | **已关闭** | **附录 A**：URS Must → 模块/接口/实体，逐条 45 项（与 URS MVP Must 计数一致） |
| DS-003 | P1 | **已关闭** | §11 可观测性专节（结构化日志字段、指标、脱敏） |
| DS-004 | P1 | **已关闭** | §4.1.1 `RobotStatus` 强制字段 + Fake 注入 + 急停→Failed/释放锁 |
| DS-005 | P1 | **已关闭** | §6.1 任务状态迁移表；§6.2 `ApprovalRequest` 状态机 + `e_sign=false` 旁路 |
| DS-006 | P1 | **已关闭** | §4.2 MVP 最小 API 资源表 + 错误码初稿 |
| DS-007 | P1 | **已关闭** | §5.1 `idempotency_key` 规则与 Upsert |
| DS-008 | P1 | **已关闭** | §10.1 报警 WebSocket + ack/close 权限码 |
| DS-009 | P1 | **已关闭** | §10.2 备份范围冻结 + TC-MVP-09 引用 |
| DS-010 | P2 | **已关闭** | 文首权威声明 + §13 目录引用 scheme §4.2（`backend/app/adapters/`） |
| DS-011 | P2 | **已关闭** | §4.3 锁定 WebSocket |
| DS-012 | P2 | **已关闭** | §14 三张 mermaid 时序（含电梯 ElevatorAdapter 路径） |
| DS-013 | P2 | **已关闭** | §5.2 时序库决策门槛 |

**交叉一致性（三项 P0 联动）**

1. **里程碑权威**：文首声明「里程碑以 `ref/plan.md` §1.2 为准」；§12 决议表同步 — 与 plan/scheme 一致。
2. **ElevatorAdapter**：与 `project_scheme.md` §2.1/§4.3/§4.4 `elevators[]`、`plan.md` TC-MVP-11 / WBS Fake 表述一致；scheme 配置示例与 DS §7 示意对齐。
3. **URS 追溯**：附录 A 与 plan §6.3 TC 映射可互证（如 ROB-007→TC-MVP-11，DAT-005→TC-MVP-05）。

## 3. 符合项（V0.4 保持/增强）

- 电梯模型全文统一为**独立 ElevatorAdapter**，消除 V0.3 §4.1 与 §7 自相矛盾。
- 附录 A 满足 `AGENTS.md`「需求→设计」可追溯要求；Must 全覆盖，Should/Could 在表后脚注区分，不混淆门禁。
- Gateway / 适配层边界、MVP 直连、简单互斥、批准流与签名开关、目录/里程碑双权威声明与 scheme/plan V0.4 对齐。
- §9 审计只追加策略与 URS-AUD-003 设计要点一致（Should 项在 TC-MVP-21 可书面豁免）。
- §14 电梯时序明确调度→ElevatorAdapter，不再经 AmrAdapter 转发。

## 4. 问题清单（残留 / 观察项）

| ID | 严重级别 | 位置 | 问题描述 | 建议 |
|----|----------|------|----------|------|
| DS-R01 | P2 | 附录 A | **URS-ROB-003**、**URS-NFR-002** 标「部分」：低电量阈值默认值、杀进程恢复实现细节仍随 M1–M3 实现冻结 | M2/M3 实现评审时关闭为「已设计」；依赖 TC-MVP-23 / HIL 补证 |
| DS-R02 | P2 | 文档头 `状态: Draft` | V0.4 内容已达 M0 基线，但版本状态未升为 Approved/Baseline | M0 收口时由 PM 更新状态或附评审纪要 |
| DS-R03 | P2 | 附录 A 脚注 | **URS-NFR-001**（Should）仅脚注「M4 前 Fake 全链路 P95」；plan 无独立 TC | M4 前在 `doc/test.md` 记录基线或单列性能探测任务（非 M0 阻塞） |
| DS-R04 | P2 | URS-ALM-002 | Should 项：确认/关闭权限已在 §10.1 与 API 表体现；生命周期状态机未单独枚举 | M2 报警模块设计时可补 5 行状态表（可选） |

**无未关闭 P0；无阻塞 M1 的关键 P1。**

## 5. 需求追溯抽检

- 抽检 Must ID：ROB-007、ROB-009、DAT-005、ADP-003、API-004、BAK-002 — 附录 A 均有落点且与正文章节一致。
- 与 `urs.md` 计数：MVP **Must 45 条**，附录 A 主表 **45 行** — 一致。
- V0.3 审核 §5 所列缺口（ROB-005/009、DAT-005、AUD-003 等）在 V0.4 正文或附录中已闭合或标为 Should/脚注。

## 6. 与其他文档一致性

| 维度 | 结论 |
|------|------|
| plan §1.2 里程碑 | DS 不另定义；声明一致 |
| scheme §4.2 目录 | DS §13 引用 scheme 为权威 — 一致 |
| scheme §4.4 / §5 电梯与资源锁 | 与 DS §4.1、§6、§8 一致 |
| plan TC-MVP-11/12/19 | 与 DS 电梯/互斥/急停设计一致 |

## 7. 结论与建议

- **总体结论：通过。**
- 建议将 DS V0.4 作为 M1 起适配层/Gateway/领域模块开发的**设计硬基线**。
- M1 契约冻结评审时重点核对：附录 A 中「部分」两项是否随接口与持久化设计关闭。

## 8. 后续验证关注点（进入 M1 后）

- `AdapterFactory` 是否同时注册 `elevator_fake` 与 Amr/仪表 Fake；编排仅经 ElevatorAdapter 调用电梯技能。
- OpenAPI 草图是否覆盖 §4.2 最小资源表路径与权限码。
- E2E 日志是否含 `request_id`/`task_id`/`robot_id`（§11）。
- Fake 急停注入与 TC-MVP-19 用例一致。
