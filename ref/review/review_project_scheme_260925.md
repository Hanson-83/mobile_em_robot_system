# 技术方案（project_scheme）审核意见（2026-09-25）

## 1. 审核元信息
- 审核对象：`ref/project_scheme.md`（工作区副本 `docs/project_scheme.md`）V0.3 / MER-SCHEME-001
- 审核依据：`AGENTS.md`、`requirement.md`、`urs.md` V0.3、`ds.md` V0.3；工程规范全套；并对照 `plan.md`
- 审核人：Reviewer_Max
- 审核日期：2026-09-25
- 总体结论：**有条件通过** — 定位与分期正确、外部系统假设清晰、配置示意与 Gateway/直连决议对齐 URS，但与 `plan.md` 的里程碑编号严重冲突，且实现级细节（调度、幂等、可观测性、电梯设备配置）不足以单独指导编码，需先对齐里程碑并补齐关键方案缺口。

## 2. 总体评价

`project_scheme.md` 符合 `AGENTS.md`「技术正文由 plan 引用、不重复规划全文」的角色：把硬件选型章改为「外部系统与集成假设」、明确不做清洁与不做选型结论，与 URS/DS 的上位机边界一致。模块目录、`devices.example.yaml` 示意、看板要点和部署原则对启动脚手架有帮助。

主要问题是 **§9 里程碑与 `plan.md` §1.2 对 M4–M7 的定义错位**（联调门禁、扩展、臂 PoC 编号互换/合并），属 P0 一致性缺陷，会导致排期与验收门禁读错。其次，方案对调度互斥算法、续传幂等、结构化日志、OpenAPI 最小面、电梯适配器配置等仍停留在「见 DS」级别，作为「技术方案」可执行性偏弱。

建议以 plan 里程碑为权威源修订 §9，补齐与 DS 统一后的电梯/目录/幂等方案，并增加可观测性与质量门禁引用后升为实施基线。

## 3. 符合项（做得好的地方）
- 路径与角色符合 `AGENTS.md`：`ref/project_scheme.md`，由 `plan.md` 引用。
- §1「明确不做」清单正确：清洁、硬件选型/BOM、改装清单均排除。
- §2 外部系统表把用户职责与上位机期望拆开，避免把硬件验收混入软件交付。
- §2.2 对内拓扑决议（MVP 直连、边端须端侧缓存）与 URS/DS 一致，且强调「不对等默认」。
- §4.2 monorepo 目录清晰，Gateway 路由分组、domain/adapters/services 分层符合 `tech_stack.md` / `coding_standards.md`。
- §4.4 配置示例含 `access_mode: direct`、`e_sign: false`、`resource_mutex: simple`，可直接作 `devices.example.yaml` 起点。
- §7 他厂对比坚持「只借鉴上位机思路」，符合 URS §6 假设。
- 技术栈（FastAPI + Vue 3 + TS + Vite + uv）与 DS/URS 锁定一致，并声明不修改全局 `tech_stack.md`。

## 4. 问题清单

| ID | 严重级别(P0/P1/P2) | 位置/章节 | 问题描述 | 依据（URS/requirement/规范条款） | 整改建议 |
|----|-------------------|-----------|----------|----------------------------------|----------|
| SCH-001 | P0 | §9 里程碑 | **与 plan.md 里程碑严重不一致**：scheme 将 M4=多端契约+Web 冻结、M5=设备联调、M6=扩展仪表/交通、M7=臂 PoC；plan 将 M4=Web MVP 冻结、M5=Gateway/多端契约、M6=联调门禁、M7=扩展/远期。同一项目两套里程碑语义，排期与门禁会冲突。 | `AGENTS.md` plan 引用 scheme；内部一致性；URS 分期 | **以 `plan.md` §1.2 为权威**重写 scheme §9；scheme 只列「该里程碑的软件交付物」，编号与名称必须与 plan 逐字对齐。 |
| SCH-002 | P0 | §4.4；§5.4 电梯 | **电梯如何配置进 devices 未说明**：功能开关 `elevator_skills: true` 有，但无 `elevators[]` 或适配器 type；叠加 DS 中 AmrAdapter 挂电梯方法 vs ElevatorFake 独立实现的歧义，方案无法指导装配。 | URS-ROB-007；DS §4.1/§7；`interface_contracts.md` | 与 DS 统一电梯模型后，在 YAML 示例增加电梯设备块（如 `elevators: [{id, adapter: elevator_fake, ...}]`）及调度如何占用资源锁的说明。 |
| SCH-003 | P1 | §5 调度 | **简单互斥仅一句话**，无锁粒度、排队 vs 失败策略、死锁规避（如电梯+点位嵌套锁顺序）、与集群任务同步屏障的关系。开发易各写各的。 | URS-SCH-003；DS §6 | 增加「资源锁方案」小节：资源类型枚举、获取/释放时机、超时、冲突策略配置项；给出 2 机争用同一点位的伪流程。 |
| SCH-004 | P1 | §6 缓存续传 | 仅写「队列 + 幂等键 Upsert」，**无键规则、队列落盘位置、MVP 直连场景下重试责任方**（适配层 vs 领域服务）。 | URS-DAT-005；DS §8 | 明确 MVP：适配层/采集管道生成 `idempotency_key`，数据服务 Upsert；给出键字段与重试退避上限；边端补传标为扩展并引用 URS-INS-009。 |
| SCH-005 | P1 | 全文缺专节 | **无可观测性/日志/指标方案**，未引用 `observability.md`。部署章有 NTP，但无日志格式、关联 ID、健康检查设计。 | `observability.md`；`engineering_spec.md` 部署；URS-NFR-004 | 增加简短「日志与健康检查」：结构化日志、`/health`、任务 ID 贯通；容器/systemd 日志出口约定。 |
| SCH-006 | P1 | §4.3 Gateway | Gateway 能力停留在「鉴权、限流、OpenAPI」口号，**无限流阈值、Token 模型、与 RBAC 权限码映射、版本策略落地步骤**。 | URS-API-001..004；URS-SEC-003；`security.md` | 补充：Bearer/API Token 模型；MVP 限流默认值（可配置）；权限码与 operations/data/settings 分组对应表；破坏性变更走 v2 的发布约定。 |
| SCH-007 | P1 | §4.2 vs DS §11 | 目录：scheme 为 `backend/app/adapters/`，DS 写顶层 `adapters/`。脚手架若各写各的会分叉。 | 内部一致性；`engineering_spec.md` | 声明本文件目录为仓库权威布局；提请 DS 同步修改（见 DS-010）。 |
| SCH-008 | P1 | §8 部署；缺安全落地表 | 部署未提 `.env.example`、密钥注入、默认鉴权开启、TLS(TBD) 的 MVP 态度（内网明文是否允许）。与 `security.md` 衔接弱。 | `security.md`；URS-NFR-003/007 | 增加部署安全清单：`.env.example` 占位、禁止密钥入库、MVP 内网 HTTP 需书面风险接受或强制 TLS 二选一写明。 |
| SCH-009 | P2 | §6 导出 | CSV/Excel、PDF 均「轻微 TBD」，方案未给临时默认，报告模块选型（库）空白。 | URS-RPT-003；URS-ALM-003 | MVP 建议默认：报警/数据导出 CSV；报告 HTML→PDF（或先 HTML 归档），并写进开放问题关闭条件。 |
| SCH-010 | P2 | §9 M4 表述 | 即便对齐编号前，单行「多端契约稳定；Web MVP 功能冻结」把 plan 的 M4/M5 揉在一起，语义含混。 | plan §1.2 | 拆分后删除合并表述。 |
| SCH-011 | P2 | §3 监测数据 | 领域命令与 DS 一致，但缺 **质量位/无效值**、采样失败是否写 Measurement 的约定。 | URS-DAT-001；`interface_contracts.md` | 在 Measurement 方案中增加 `quality` 枚举与失败不落数/落数带 quality=bad 的策略。 |

## 5. 需求追溯缺口

| 来源 | 缺口 |
|------|------|
| URS-SCH-004/005 | 地图导入格式、点位 CRUD API、位姿刷新频率仅原则，无方案级约定 |
| URS-ROB-005 | 断线事件与任务恢复/失败策略未写清 |
| URS-AUD-002 | 批准流模块在 §4.1「见 DS」，方案层无页面/API/状态说明，前后端难并行 |
| URS-BAK-001/002 | §8 备份一句带过，无作业调度（cron/systemd timer）与演练频率 |
| URS-CLI-001 | Vue Web 信息架构/页面清单缺失（地图、任务、看板、报警、配置、用户） |
| URS-NFR-002 | 「杀进程后任务状态不丢失」无持久化/恢复方案要点 |
| requirement 2.1 集群 | 集群任务在分期中有，方案对「同步屏障可选」无示例 |
| 扩展浮游菌 | §3 一行，可接受；建议指向扩展里程碑交付物 |

未见把清洁机或硬件选型写回方案 — 符合范围。

## 6. 与其他文档的一致性问题
- **P0：里程碑 M4–M7 与 plan 冲突**（SCH-001）— 三份文档中最严重的一致性问题。
- **电梯配置/适配模型**与 DS 歧义共振（SCH-002 / DS-001）。
- **目录结构**与 DS §11 不一致（SCH-007）。
- 决策关闭清单（签名/Gateway/直连/电梯/互斥/Vue）与 URS §7、DS §12、plan §8 一致 — 良好。
- 开放问题列表与 URS §7 基本同构 — 良好。

## 7. 优先整改清单（按优先级）
1. **P0**：按 `plan.md` 重写 §9 里程碑表，消除 M4–M7 错位。
2. **P0**：与 DS 统一电梯适配与 YAML 配置示例，补齐 Fake 装配说明。
3. **P1**：补资源锁方案、续传幂等规则、Gateway 鉴权/限流/权限映射、可观测性与部署安全清单；声明目录权威并通知 DS 对齐。
4. **P2**：导出格式临时默认、Measurement quality、Vue 页面清单（可附 plan 或单独 UI 大纲）。

## 8. 后续验证关注点
- 脚手架初始化是否严格按 §4.2 目录落地，且 CI 能跑 Fake 冒烟（含电梯）。
- `access_mode=direct` 路径可测；不得出现 MVP 强制边端。
- 简单互斥在 ≥2 Fake 机器人下可演示冲突与排队/失败。
- Gateway OpenAPI 三分组与 RBAC 拒绝路径可测。
- 部署文档含备份恢复与 `.env` 注入；密钥扫描不进仓。
- 里程碑门禁文案与 plan/测试用例编号一致，避免「M5 联调」歧义。
