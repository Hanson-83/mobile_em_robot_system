# 项目规划（plan）审核意见（2026-09-25）

## 1. 审核元信息
- 审核对象：`ref/plan.md`（工作区副本 `docs/plan.md`）V0.3 / MER-PLAN-001
- 审核依据：`AGENTS.md`、`requirement.md`、`urs.md` V0.3、`ds.md` V0.3、`project_scheme.md` V0.3；`testing_quality.md` 等工程规范
- 审核人：Reviewer_Max
- 审核日期：2026-09-25
- 总体结论：**有条件通过** — 作为上位机软件规划，目标/WBS/依赖/测试映射整体扎实，Fake 主路径与 HIL 并行门禁策略正确；但与 `project_scheme.md` 里程碑冲突必须先消除，且若干 URS Must 缺少对应验收用例、日历与跟踪文档未落地，需整改后作为执行基线。

## 2. 总体评价

plan V0.3 符合 `AGENTS.md` 对规划文档的定义：基于 requirement/URS，引用 `project_scheme.md` 承载技术方案，并**包含测试方案**（§6）及 URS 映射摘要，这是三份待审文档中对「可验证」支持最好的一份。WBS 已剔除硬件选型、里程碑将真机联调解耦为并行门禁，与 URS 范围决议一致。

主要缺陷：① 被引用的 `project_scheme.md` §9 里程碑与本文 §1.2 **不一致**，计划权威性被削弱；② §6.3 验收用例未覆盖部分 MVP Must（地图可视化、趋势、急停、会话监测、报警导出、审计防篡改等）；③ 具体日历 TBD、且未按 `AGENTS.md` 要求衔接 `progress.md` / `risks.md` / `tasks.md` 的持续跟踪机制。优先级列表将两项都标 P0 但未区分紧急序，执行时仍需再拆。

总体可「有条件通过」：补齐里程碑对齐与用例缺口、挂上进度/风险跟踪后即可驱动 M1 开工。

## 3. 符合项（做得好的地方）
- 定位正确：`ref/plan.md`，技术方案外置引用，避免与 scheme 正文重复。
- 范围仅上位机；硬件 Owner 外置；电梯 Fake 不可豁免、真机可豁免 — 与 URS-ROB-007 / 质量门禁表述一致。
- §3 WBS 与 §4 依赖图清晰，Gateway 与契约并行于调度，符合工程现实。
- §6 测试分层对齐 `testing_quality.md`（单元/集成/E2E/HIL 跳过 CI）。
- Fake 要求具体（Amr/Particle/Climate/Airflow/Elevator），可直接变成开发任务。
- TC-MVP-01..15 覆盖签名批准流、Gateway、直连、简单互斥、电梯 Fake 等关键决策点 — 质量高。
- §7 风险表务实（API 延期、范围蔓延、合规期望过高）。
- §8 立即行动可执行，且声明开放决策已关闭。

## 4. 问题清单

| ID | 严重级别(P0/P1/P2) | 位置/章节 | 问题描述 | 依据（URS/requirement/规范条款） | 整改建议 |
|----|-------------------|-----------|----------|----------------------------------|----------|
| PLN-001 | P0 | §1.2；对照 scheme §9 | **里程碑 M4–M7 与 project_scheme 定义冲突**（见 SCH-001）。计划写 M5=Gateway 稳定、M6=联调；scheme 写 M5=联调、M6=扩展。双源真相。 | `AGENTS.md`「plan 引用 scheme」；内部一致性 | 在 plan 中明确「里程碑定义以本文 §1.2 为准」，并要求 scheme §9 同步修改；或两文合并为同一张表避免漂移。 |
| PLN-002 | P0 | §6.3 用例表 | **部分 URS MVP Must 无对应用例**：如 URS-SCH-004/005（位姿/地图可视化）、URS-DAT-002（实时/历史趋势）、URS-ROB-005（会话/断线）、URS-ROB-009（急停）、URS-ALM-003（历史导出）、URS-AUD-003（审计防篡改）、URS-RPT-002（组合/集群报告 Should 但 MVP 阶段列出）、URS-CLI-001（浏览器完成核心操作 E2E）。门禁「Must 通过」无法核对。 | URS 对应 ID；`testing_quality.md`；URS-NFR-006 | 扩展 TC-MVP-16+：地图与位姿、趋势看板、断线重连、急停注入、报警导出、审计只追加、Vue 核心路径 E2E；Should 项可标「可书面豁免」但须显式列出。 |
| PLN-003 | P1 | §1.2 日期 | 全部里程碑「日期待排期 / 日历 TBD」，无即使是相对工期（人周）或顺序时间盒。难以资源评估与进度追踪。 | `AGENTS.md` progress/tasks；项目工作流 | 增加相对工期列（如 M1: 1–2 周）或依赖「用户设备就绪日 T0」的相对日程；绝对日期可仍 TBD。 |
| PLN-004 | P1 | 全文；AGENTS 文档化 | **未建立/引用进度与问题跟踪文档**（`ref/progress.md`、`risks.md`、`tasks.md`）。plan §8 提到 `progress.md`，但规划未要求初始化这些文件，违背手册「进度与问题追踪」习惯。 | `AGENTS.md` progress/issues/risks/tasks | 在 §8 增加：初始化 `ref/progress.md`（及必要时 tasks/risks），并规定每个里程碑结束更新。 |
| PLN-005 | P1 | §4 优先级 | 两条并列 **P0**（适配层 Fake 全链路 vs 编排状态机+Vue 骨架），无先后/并行规则，易争资源。 | `engineering_spec.md` 小步交付 | 改为：P0a 契约+Fake+Gateway 草图 → P0b 状态机+互斥+电梯 Fake → P0c Vue 骨架；或明确可并行的人员拆分。 |
| PLN-006 | P1 | §6.4 质量门禁 | 门禁未显式勾选 `testing_quality.md` DoD（lint/类型检查、契约文档更新、无密钥 diff）。与工程规范完成定义脱节。 | `testing_quality.md` DoD | 在 §6.4 增加 DoD 条目：lint/typecheck、相关单测、OpenAPI/配置 schema 已更新、无密钥入库。 |
| PLN-007 | P1 | §6.3 | **缺「批准流+限值变更」与「报告批准」独立用例细节**；TC-MVP-13 较粗，未列默认 `e_sign=false` 出厂配置检查（URS-AUD-004）。 | URS-AUD-002/004 | 拆分为：关签名主流程；开签名改限值被拦截直至批准；默认配置断言 `features.e_sign == false`。 |
| PLN-008 | P1 | §5 角色；缺前端信息架构任务 | WBS-6「Vue Web」无页面/故事拆分，难估点与验收。 | URS-CLI-001；requirement 2.1–2.5 UI | 在 WBS 或 tasks 中列出 MVP 页面：登录、地图监控、任务编排、点位/限值、实时趋势、报警、报告、用户权限、系统开关。 |
| PLN-009 | P2 | §6.1 | 「夜间可选」仿真无责任人/频率；不稳定测试治理未提。 | `testing_quality.md` 闪烁测试 | 约定互斥/续传仿真至少在 M2/M4 各跑通一次；禁止长期 skip 关键 Must 用例。 |
| PLN-010 | P2 | §7 风险 | 缺「plan/scheme 文档漂移」「开放 TBD 永久化（时序库/PDF）」类文档风险。 | 第一性原理；URS §7 | 风险表增加：双文档里程碑漂移（缓解：单一权威表）；TBD 超期未关则升级为 issues。 |
| PLN-011 | P2 | §2 引用 | 写「验收以 urs.md ID 为准」，但未要求测试记录文档路径（`doc/test.md`）。 | `AGENTS.md` test.md | 增加：验收执行记录写入 `doc/test.md`（或等价），并追溯 URS ID。 |

## 5. 需求追溯缺口

| URS/requirement | plan 中状态 |
|-----------------|-------------|
| URS-SCH-004/005 地图与位姿 | WBS-4 提及，**无 TC** |
| URS-DAT-002 趋势可视化 | WBS-4 提及，**无 TC** |
| URS-ROB-005/009 会话与急停 | 风险/Fake 故障注入部分覆盖，**无显式 TC** |
| URS-ALM-003 导出 | 未映射 |
| URS-SEC-002 安全策略 | WBS-5 含权限，策略细则与用例弱 |
| URS-AUD-003 防篡改 | 未映射 |
| URS-NFR-001 性能 | 未规划基线采集任务 |
| URS-NFR-002 任务恢复 | 未单独测试项（建议杀进程恢复 TC） |
| requirement 2.7 备份 | 有 TC-MVP-09 — 良好 |
| requirement 硬件 1.x | 正确移出 — 良好 |
| 远期臂/浮游菌 | 有 M7/TC-EXT — 良好 |

## 6. 与其他文档的一致性问题
- **与 project_scheme：里程碑 M4–M7 冲突（P0）** — 必须先修。
- 与 DS/URS：决策项（Gateway、直连、电梯 Fake、简单互斥、批准流、Vue）一致 — 良好。
- 测试用例命名与 URS ID 映射总体正确；缺口见 PLN-002。
- plan 依赖「编排状态机草案」「批准流设计」但这些细表在 DS 仍过粗 — 需与 DS P1 整改联动，否则 §8 行动项产出质量不稳。
- 引用 `progress.md` 但工作区审核包未提供该文件 — 规划应要求创建。

## 7. 优先整改清单（按优先级）
1. **P0**：与 scheme 对齐里程碑；在 plan 声明权威源并改 scheme。
2. **P0**：按 URS MVP Must 补全 TC 列表（地图/趋势/断线/急停/导出/审计防篡改/Vue E2E/进程恢复等）。
3. **P1**：相对工期或时间盒；初始化 progress/tasks/risks；拆分 P0 优先级；门禁并入 testing DoD；细化签名默认关与批准流用例；Vue 页面拆分。
4. **P2**：仿真频率、文档漂移风险、`doc/test.md` 验收记录约定。

## 8. 后续验证关注点
- M4 冻结时：电梯 **Fake** 必过、真机 HIL 不阻塞；门禁清单与 URS Must 逐条打勾。
- CI 默认：单元+集成+含电梯的 Fake 冒烟；HIL 标记跳过。
- 任何「书面豁免」必须写清 URS ID、理由、补测计划，禁止口头豁免。
- 用户硬件 API 延期时，仅移动 M6 联调，不回退 M4 软件范围。
- 每个里程碑结束更新 `progress.md`，并核对 scheme/plan 里程碑表未再漂移。
- 开发启动前确认 DS 电梯边界与幂等键已按审核整改，避免计划任务空转。
