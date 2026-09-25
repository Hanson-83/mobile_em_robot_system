# 设计规范（DS）审核意见（2026-09-25）

## 1. 审核元信息
- 审核对象：`doc/spec/ds.md`（工作区副本 `docs/ds.md`）V0.3 / MER-DS-001
- 审核依据：`AGENTS.md`、`requirement.md`、`urs.md` V0.3；`engineering_spec.md`、`tech_stack.md`、`coding_standards.md`、`testing_quality.md`、`security.md`、`observability.md`、`interface_contracts.md`、`spec_README.md`；并对照 `plan.md`、`project_scheme.md`
- 审核人：Reviewer_Max
- 审核日期：2026-09-25
- 总体结论：**有条件通过** — 上位机范围、Gateway/适配层/直连拓扑/电梯 Fake/简单互斥/签名批准流等关键决策已与 URS V0.3 对齐，但存在电梯适配边界歧义、缺少 URS→设计追溯与可观测性设计、若干可执行契约细节不足，需整改后再作为开发硬基线。

## 2. 总体评价

DS V0.3 已把「仅上位机软件」边界写清楚，并正确区分 **对外 API Gateway** 与 **对内适配层**；MVP 直连、边端为演进、多机简单互斥、电子签名开启强制批准流、前端锁定 Vue 等决议与 URS 一致，可作为架构讨论基线。

作为「指导后续开发与验证」的设计规范，当前仍偏架构概要：适配器方法清单与数据实体表有，但缺少 URS ID 到模块/接口的追溯矩阵、关键流程时序、批准流/任务状态机细表、结构化日志与错误目录，以及急停等安全状态字段约定。`interface_contracts.md` / `observability.md` 要求的契约与可观测性在 DS 中落实不足。

与 `plan.md` / `project_scheme.md` 在「电梯归属 AmrAdapter 还是独立 ElevatorAdapter」上表述不一致风险高；三份文档里程碑编号冲突虽主要在 plan/scheme，但 DS 引用方案目录却未约束里程碑对齐，开发排期易误读。建议按下方 P0/P1 清单补齐后再冻结 V0.4。

## 3. 符合项（做得好的地方）
- 符合 `AGENTS.md` 对 `ds.md` 的定位（`/doc/spec/ds.md`，由 URS 生成），范围收窄为上位机，硬件外置为 External Systems。
- 与 URS V0.3 已关闭决策高度一致：API Gateway、MVP 直连、电梯纳入 MVP（技能+Fake）、简单互斥、签名+批准流、Vue 锁定。
- §2 架构图与 §3 分层职责清晰，Gateway 与 Adapter「不可混用」表述正确，对齐 `tech_stack.md` / `interface_contracts.md`「适配层解耦」原则。
- §4.1 适配器方法清单、错误 `retryable`、坐标系/单位在边界转换、禁止厂商私有帧泄漏 — 符合接口契约规范。
- §9 安全设计与 `security.md` 一致：密钥外置、默认鉴权、签名建议默认关；不声称 Part 11 已获证。
- §11 技术栈落地明确「本项目覆盖 Vue、不改全局 `tech_stack.md`」，符合 `spec_README.md`「项目特例写在 README/ref」的精神。
- §12 风险表将多项 TBD 标为已决议或轻微 TBD，开放问题收敛良好。

## 4. 问题清单

| ID | 严重级别(P0/P1/P2) | 位置/章节 | 问题描述 | 依据（URS/requirement/规范条款） | 整改建议 |
|----|-------------------|-----------|----------|----------------------------------|----------|
| DS-001 | P0 | §4.1 AmrAdapter；§7 ElevatorFake | **电梯适配边界歧义**：§4.1 将 `call/enter/exit_elevator` 挂在 `AmrAdapter` 上，§7 又出现独立 `ElevatorFake / ElevatorVendorX`。开发无法判断电梯是 AMR 子能力还是独立适配器，影响 Fake、配置 schema 与 `URS-ROB-007` 实现。 | URS-ROB-007；`interface_contracts.md`「每个外部系统对应清晰适配器」 | 明确一种模型并全文统一。推荐：**独立 `ElevatorAdapter`**（技能由调度编排调用），`AmrAdapter` 仅保留导航/充电/遥测；或文档声明「电梯经 AMR 厂商聚合 API 时由 AmrAdapter 转发，另提供 ElevatorAdapter 直连楼控」并给出配置装配规则。同步改 `project_scheme.md` 配置示例。 |
| DS-002 | P0 | 全文（缺章节） | **缺少 URS→DS 需求追溯矩阵**。URS 数十条 Must（如 ROB-005/009、DAT-005、AUD-002、API-001..004）在 DS 中以叙述覆盖，无法逐条核对「设计是否已落地、落在哪一模块」。阻碍验收与有条件通过闭环。 | URS 全文 Must；`AGENTS.md` 开发工作流「需求→设计」；`testing_quality.md` 行为可测 | 新增「附录 A：URS ID → 模块/接口/实体」表，至少覆盖全部 MVP Must；标明「已设计 / 部分 / TBD」。 |
| DS-003 | P1 | 缺专节；§5 AuditEvent 仅有 request_id | **可观测性设计缺失**：未规定结构化日志字段、任务/请求关联 ID 贯穿链路、关键指标（调度延迟、适配器成功率、队列长度）、日志级别与脱敏。与 `observability.md` 不对齐，运维与排障无设计抓手。 | `observability.md`；URS-NFR-004；URS-ROB-005 | 新增「可观测性」专节：标准 `logging`、必选字段（ts/level/module/request_id/task_id/robot_id）、禁止记录密钥/完整原始报文；列出 MVP 最小指标集。 |
| DS-004 | P1 | §4.1；§5 RobotStatus | **急停/故障安全状态未在契约中点名**。URS-ROB-009 要求急停/故障可测（Fake 可注入），DS 仅笼统 `get_status() -> RobotStatus`，未定义必选字段与任务中断策略挂钩点。 | URS-ROB-009；`interface_contracts.md`「急停与幂等语义」 | 在 `RobotStatus`（或等价 DTO）中强制字段：`estop`、`fault_code`、`fault_msg`、`mode`；规定 Fake 注入方式及调度侧「急停→中断/失败」策略引用。 |
| DS-005 | P1 | §6 状态机；§3/§9 批准流 | **任务状态机与批准流状态机过粗**。任务仅示意 `Created→…→Succeeded|Failed|Cancelled`，暂停 TBD；批准流无状态枚举、超时、驳回、多人审批规则。签名开启场景无法直接编码。 | URS-SCH-001/002；URS-AUD-002 | 补任务状态迁移表（含取消/失败回充）；补 `ApprovalRequest` 状态：`Draft→Pending→Approved|Rejected|Expired`；明确「限值变更/报告批准」绑定点与关闭签名时旁路路径。 |
| DS-006 | P1 | §4.2；缺 OpenAPI 最小资源表 | **对外 API 仅有分组名**（operations/data/settings），无最小资源/路径草表（任务、点位、测量、报警、鉴权、报告）。不足以指导 M1 Gateway/OpenAPI 草图与前后端并行。 | URS-API-001..004；`interface_contracts.md`「OpenAPI/稳定错误模型」 | 增加 MVP 最小 API 资源表（方法+路径前缀+权限码+分组）；错误码枚举初稿（鉴权失败、互斥冲突、设备离线、不可重试参数错等）。 |
| DS-007 | P1 | §5 Measurement；§8 断点续传 | **断点续传幂等键未设计到字段级**。仅原则性描述「幂等接收」，未定义幂等键构成（如 `device_id+sample_id+ts` 或 `client_request_id`）与 Upsert 冲突策略。 | URS-DAT-005；`observability.md` 幂等/状态机 | 在数据模型中增加 `idempotency_key`（或等价唯一约束）；写明生成规则、重复上报行为（忽略/合并）、与任务实例关联方式。 |
| DS-008 | P1 | §3 报警事件「通知通道」 | **报警通知通道未设计**：仅写「通知通道」，无 WebSocket/站内/邮件等 MVP 范围；`URS-ALM-002` 确认/关闭权限也未落到权限码。 | URS-ALM-001/002；URS-SEC-001 | 明确 MVP 通知=实时通道（WS/SSE）+ 历史查询；确认/关闭所需权限码；扩展通道标为 Could。 |
| DS-009 | P1 | §10；缺专节 | **备份范围与恢复验收未设计**：`BackupSet.scope` 存在但范围仍 TBD；与 URS-BAK 验收「恢复演练」不对齐，运维无法实现作业。 | URS-BAK-001/002；`security.md` 高风险操作 | 冻结 MVP 备份范围建议：PostgreSQL 业务库 + `config/` + 报告文件目录；恢复步骤与校验清单引用 plan 测试用例 TC-MVP-09。 |
| DS-010 | P2 | §11 目录；对比 scheme §4.2 | **仓库目录表述不一致**：DS 写 `backend/` `frontend/` `adapters/`，`project_scheme.md` 将 `adapters/` 放在 `backend/app/adapters/`。易造成脚手架路径分歧。 | `engineering_spec.md` 可复现结构；内部一致性 | DS 改为引用 scheme 目录为唯一权威，或双方统一为 `backend/app/adapters/`（推荐与 scheme 一致）。 |
| DS-011 | P2 | §4.3 实时通道 | WebSocket **与** SSE 并列未选型，增加前端与 Gateway 双实现成本。 | URS-SCH-004；`engineering_spec.md` 小步交付 | MVP 锁定一种（建议 SSE 或 WS 二选一写死），另一种列入扩展。 |
| DS-012 | P2 | 缺章节 | **无关键业务时序图**（下发任务→导航→采样→入库→报警→报告；电梯 Call/Enter/Exit；签名批准流）。新人难把模块串起来。 | `engineering_spec.md`「先厘清边界与接口」 | 增加 2–3 张 mermaid sequence（任务主路径、电梯、批准流）。 |
| DS-013 | P2 | §5 物理库 | 时序存储「轻微 TBD」可接受，但未给出 **决策触发条件**（数据量/保留期/查询模式）。 | URS §7 开放问题 2；第一性原理 | 写明「MVP 用 PG 分区表；当保留期>X 或写入 QPS>Y 时评估 Timescale」类决策门槛。 |

## 5. 需求追溯缺口

| URS ID | 缺口说明 |
|--------|----------|
| URS-ROB-005 | 会话监测/断线错误与重连策略仅 §8 原则提及，无状态机与事件类型设计 |
| URS-ROB-009 | 急停/故障字段与 Fake 注入未在契约点名（见 DS-004） |
| URS-ROB-003 | `dock_charge` 有方法，但低电量策略阈值、触发器归属（调度 vs 机器人自管）未设计 |
| URS-DAT-002 | 可视化仅落到前端职责一行，无看板组件/查询 API 设计要点 |
| URS-DAT-005 | 幂等键字段缺失（见 DS-007） |
| URS-ALM-003 | 历史导出格式与权限未设计 |
| URS-RPT-002/003 | 组合/集群报告结构、PDF 生成组件边界过粗 |
| URS-SEC-002 | 密码策略/会话超时仅「细则 TBD」，无配置项占位 |
| URS-AUD-003 | 「防篡改取向」未落到存储策略（追加表、禁止 UPDATE/DELETE 的 DB 角色） |
| URS-INS-007 | 校准登记（Could/扩展）— DS 未占位，可标「扩展不阻塞」但建议实体预留 |
| URS-NFR-001 | 性能指标 TBD — 应注明试点基线采集方法，避免永久悬空 |
| requirement 2.9 | 多客户端 — DS 已分期，符合；桌面/移动仅占位，可接受 |

**过度设计**：未见明显过度微服务或边端双模对等默认；边端写为演进正确。  
**边界**：硬件选型不写进 DS — 正确。勿把清洁功能写回 — 已遵守。

## 6. 与其他文档的一致性问题
- **电梯适配模型**：DS §4.1 vs §7 自相矛盾，且与 `project_scheme.md` 配置示例（仅 `elevator_skills` 开关、无 elevator 设备条目）不对齐 → 见 DS-001。
- **目录结构**：DS §11 `adapters/` 顶层 vs scheme `backend/app/adapters/` → 见 DS-010。
- **里程碑**：plan 与 project_scheme 的 M4–M7 定义冲突（见 scheme/plan 审核）；DS 未定义里程碑但引用 scheme，建议在 DS「关联方案」注明「里程碑以 plan.md 为准」或要求两份先对齐。
- **术语**：三份文档对 Gateway/适配层/直连/边端/简单互斥用语总体一致，保持良好。

## 7. 优先整改清单（按优先级）
1. **P0**：统一电梯适配边界（独立 ElevatorAdapter 或明确聚合规则），同步 scheme 配置示例与 Fake 清单。
2. **P0**：增加 URS Must → 模块/接口追溯表，作为 V0.4 冻结前置条件。
3. **P1**：补可观测性专节、RobotStatus 急停字段、任务/批准流状态机细表、API 最小资源表、续传幂等键、报警通道与备份范围。
4. **P1**：与 plan/scheme 对齐目录与「里程碑权威源」声明。
5. **P2**：锁定 WS/SSE 其一；补时序图；写时序库选型触发条件。

## 8. 后续验证关注点
- Fake 路径是否覆盖电梯 Call/Enter/Exit 与急停注入，且不依赖真机（URS-ROB-007/009）。
- 切换 Fake↔真实适配器是否零改动编排核心；`access_mode=direct` 为唯一 MVP 验收拓扑。
- 签名 `e_sign=false` 主流程无阻塞；`true` 时限值变更/报告批准必须走批准流。
- 多机简单互斥：点位/电梯/充电桩锁冲突可测；客户端/第三方不可绕过 Gateway。
- 结构化日志与 `task_id`/`request_id` 是否在 E2E 中可关联排障。
- 备份恢复演练是否按冻结范围执行并留下记录。
