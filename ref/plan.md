# 项目规划（Plan）— 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 文档编号 | MER-PLAN-001 |
| 版本 | V0.4 |
| 日期 | 2026-09-25 |
| 作者 | PM_Max |
| 状态 | Draft |
| 范围 | **上位机（服务器 + 客户端）系统开发**；硬件选型由用户负责 |
| 依据 | `ref/requirement.md`、`doc/spec/urs.md` V0.3、`doc/spec/ds.md` V0.4 |
| 技术方案 | **详见** [`ref/project_scheme.md`](project_scheme.md)（本文引用，不重复全文） |
| 权威声明 | **里程碑定义以本文 §1.2 为准**；`project_scheme.md` §9 须与本表编号与名称逐字对齐 |

---

## 1. 目标与里程碑

### 1.1 目标

交付可试点的上位机 MVP：任务编排与多机**简单互斥**调度、数据采集可视化、报警、批报告、权限与可开关审计/签名（**开启则批准流**）、设备适配层（含 Fake 与**独立 ElevatorAdapter**）、**API Gateway** + OpenAPI 与 Vue Web 客户端（TypeScript + Vue）。真机联调（含电梯）作为**依赖用户硬件/API 就绪**的并行门禁，不阻塞 Fake 主路径。

### 1.2 里程碑（权威源）

> **权威声明（PLN-001）**：本表为项目里程碑**唯一权威定义**。`ref/project_scheme.md` §9 仅列对应软件交付物，**编号与名称必须与下表逐字一致**。`doc/spec/ds.md` 注明「里程碑以 plan.md 为准」，不另定义里程碑语义。

| ID | 里程碑 | 完成标志（软件） | 相对工期（人周，估） |
|----|--------|------------------|----------------------|
| M0 | 文档基线 | 上位机范围 URS/DS/方案/计划评审通过（含软件决策；V0.4 审核整改闭环） | 0.5–1 |
| M1 | 契约与骨架 | 适配接口草案、**API Gateway/OpenAPI** 草图、仓库骨架、Fake 冒烟（含电梯 ElevatorFake） | 1–2 |
| M2 | 调度 MVP | Fake 全链路：下发任务 → 模拟采样/电梯 → 看板/报警/报告；简单互斥可测 | 2–3 |
| M3 | 数据与合规 | 点位/限值/趋势、RBAC、审计/签名开关+**批准流**、备份恢复 | 2–3 |
| M4 | Web MVP 冻结 | URS-MVP Must（软件项）测试通过；电梯以 **Fake 验收**；真机联调不阻塞冻结 | 2–3 |
| M5 | Gateway 与多端契约 | OpenAPI 稳定版；MES/SCADA/DCS 对接能力；桌面/移动可分期立项 | 1–2 |
| M6 | 联调门禁 | 用户提供设备/电梯 API 后的适配器联调通过（并行） | 依赖用户 T0+1–4 |
| M7 | 扩展 / 远期 | 浮游菌适配；交通管制增强；臂技能接口 PoC（软件） | 按立项 |

绝对日历 **TBD**。相对工期以「用户设备就绪日」为 **T0** 时，M6 从 T0 起算；M1–M5 不依赖 T0。真机相关日期与软件里程碑解耦记录。

**Should 项书面豁免**：凡 URS Should 在 M4 门禁中豁免，须在 `doc/test.md` 显式写清 URS ID、理由、补测计划；禁止口头豁免。

---

## 2. 技术方案引用

实施与架构以 **`ref/project_scheme.md`** 为准（上位机模块、Gateway、对内拓扑、**ElevatorAdapter**、外部系统假设、看板、部署）。

设计边界以 **`doc/spec/ds.md`** 为准；验收以 **`doc/spec/urs.md`** ID 为准（软件项）。

验收执行记录写入 **`doc/test.md`**（或等价路径），并追溯 URS ID（PLN-011）。

仓库目录权威布局以 **scheme §4.2**（`backend/app/adapters/`）为准。

---

## 3. 工作分解（WBS）— 上位机

| WBS | 工作包 | 主要产出 | 阶段 |
|-----|--------|----------|------|
| 1 | 文档与范围锁定 | 评审纪要；软件决策关闭清单；V0.4 审核整改 | M0 |
| 2 | 契约与 Fake | 适配接口（Amr/**Elevator**/Particle/Climate/Airflow）、配置 schema（含 `elevators[]`）、Fake、错误模型 | M1–M2 |
| 3 | 调度编排 MVP | 技能/任务/组合/集群状态机；**简单互斥**资源锁（含电梯）；调度编排调用 ElevatorAdapter | M2 |
| 4 | 数据与看板 | 点位、时序、限值、趋势、地图可视化 | M2–M3 |
| 5 | 权限审计批准流 | RBAC、审计/签名开关、**批准流**、批报告、备份 | M3 |
| 6 | Vue Web 客户端（MVP） | 见 §3.1 页面清单；经 Gateway；WebSocket 实时通道 | M2–M4 |
| 7 | **API Gateway** | 统一入口；OpenAPI（操作/数据/设置）；鉴权；首批对接能力 | M1–M5 |
| 8 | 多端（分期） | 桌面/移动客户端 | M5+ |
| 9 | 联调（依赖用户） | 真实/录制适配器；电梯真机；HIL | M6（并行门禁） |
| 10 | 测试验证 | 见第 6 节；Fake 为主路径（含电梯/Gateway/批准流） | M1–M4 |
| 11 | 交通管制增强（演进） | 在简单互斥之上增强算法 | M7+ |

> 原「硬件选型/改装」WBS 已移出本计划；由用户硬件 Owner 单独管理。

### 3.1 Vue MVP 页面清单（PLN-008）

| 页面 | 核心能力 | 对应 URS |
|------|----------|----------|
| 登录 | 账号登录、会话 | URS-SEC-001 |
| 地图监控 | 地图、位姿、机器人状态 | URS-SCH-004/005 |
| 任务编排 | 创建/下发/取消任务与组合任务 | URS-SCH-001/002 |
| 点位/限值 | 点位 CRUD、限值配置（签名开则走批准流） | URS-DAT-003/004 |
| 实时趋势 | 实时与历史曲线 | URS-DAT-002 |
| 报警 | 实时推送、确认/关闭、历史导出 | URS-ALM-001..003 |
| 报告 | 批报告列表与下载/归档 | URS-RPT-001 |
| 用户权限 | 用户/组/角色 | URS-SEC-001 |
| 系统开关 | audit_trail / e_sign / elevator_skills 等 | URS-AUD-001/002/004 |
| 批准中心 | ApprovalRequest 列表与审批（签名开启时） | URS-AUD-002 |

---

## 4. 任务优先级与依赖

```text
文档评审(1) ─→ 契约与Fake(2) ─→ 调度+互斥+电梯(3) ─┬→ 数据看板(4) ─→ Web(6) ─→ MVP冻结(M4)
                     └→ API Gateway(7) ──────────────┤
                              └→ 权限审计批准流(5) ──┴→ Gateway稳定(M5) ─→ 多端(8)
用户设备/电梯API就绪 ────────────────────────────────→ 联调(9)〔并行门禁〕
测试(10) 贯穿 M1–M4（Fake）；HIL 跟 M6
交通增强(11) 在 MVP 后演进
```

优先级（PLN-005 拆分）：

1. **P0a**：契约 + Fake（含 ElevatorFake）+ Gateway/OpenAPI 草图 → 先于或并行启动骨架。
2. **P0b**：编排状态机 + 简单互斥 + 电梯技能编排（调用 ElevatorAdapter）→ 依赖 P0a 接口草案。
3. **P0c**：Vue Web 骨架（登录+地图壳+任务列表）→ 可与 P0b 人员并行。
4. **P1**：报警、批报告、地图可视化完善、断点续传接收、审计/签名开关、批准流、备份恢复、Gateway 对接能力。
5. **P2**：桌面/移动端；交通管制增强。
6. **P3**：浮游菌适配扩展、臂技能接口。
7. **并行**：用户硬件/电梯就绪后的真实适配器联调（不阻塞 Fake MVP）。

---

## 5. 角色建议（软件侧）

| 角色 | 职责 |
|------|------|
| PM / 架构 | 范围、里程碑、URS/DS、与用户硬件 Owner 的契约对齐；维护 progress/tasks/risks |
| 后端 | FastAPI、Gateway、调度、数据、适配层（含 ElevatorAdapter）、批准流 |
| 前端 | 看板、地图、任务与配置 UI（调 Gateway） |
| 测试 / 验证 | 分层测试、URS 追溯、Fake E2E（含电梯/Gateway/批准流）；维护 `doc/test.md` |
| 运维 | 服务器部署、备份演练 |
| QA（客户） | 限值、SOP、报告与合规开关/批准流策略 |
| 用户硬件 Owner（外部） | 设备选型、电梯硬件、API 文档、联调窗口 |

---

## 6. 测试方案

对齐 `spec/testing_quality.md`；**以 Fake/Simulator 为主路径**；真机联调为依赖用户硬件就绪的并行门禁。

### 6.1 分层策略

| 层级 | 范围 | 工具/方式 | CI |
|------|------|-----------|-----|
| 单元 | 解析、限值、状态机、错误模型、资源锁 | pytest | 默认跑 |
| 集成 | Gateway + API + 仓储；适配层 + **Fake**；批准流 | pytest + TestClient | 默认跑 |
| 端到端 / 冒烟 | 启动 → 下发任务 → Fake（含电梯）完成 → 报告/报警 | 脚本/compose | 关键冒烟 |
| 仿真 | 多机简单互斥冲突、断网续传 | Fake 注入 | **M2、M4 各至少跑通一次**（PLN-009）；禁止长期 skip 关键 Must |
| HIL | 用户设备/电梯 API/真机 | 实验室/现场 | **默认跳过 CI**；跟 M6 |
| 验收 | URS 软件 ID 用例 | 记录写入 `doc/test.md` | MVP 前 |

### 6.2 Fake / Simulator 要求（Must）

- `AmrFake`：导航耗时、电量、故障/急停注入；**不含** call/enter/exit_elevator。
- `ElevatorFake`：Call/Enter/Exit 可演；可注入失败；由调度编排经 **ElevatorAdapter** 调用。
- `ParticleFake` / `ClimateFake` / `AirflowFake`：可配置曲线与超限。
- 配置切换真实适配器不改业务代码；MVP `access_mode=direct` 可测；未来 `via_edge_agent` 为扩展。

### 6.3 验收用例与 URS 映射

| 用例 | 映射 URS | 层级 | 备注 |
|------|----------|------|------|
| TC-MVP-01 创建点位与限值 | URS-DAT-003/004 | 集成 | |
| TC-MVP-02 Fake 单机任务全流程 | URS-SCH-001/002, URS-DAT-001 | E2E | |
| TC-MVP-03 超限报警并可确认 | URS-ALM-001/002 | E2E | |
| TC-MVP-04 任务批报告 | URS-RPT-001 | E2E | |
| TC-MVP-05 断网续传幂等 | URS-DAT-005 | 仿真 | |
| TC-MVP-06 RBAC 越权拒绝 | URS-SEC-001 | 集成 | |
| TC-MVP-07 审计开关行为 | URS-AUD-001 | 集成 | |
| TC-MVP-08 Gateway 鉴权与 OpenAPI | URS-API-001/002/004, URS-SEC-003 | 集成 | |
| TC-MVP-09 备份与恢复 | URS-BAK-001/002 | 手工/脚本 | 范围：PG + config/ + 报告目录 |
| TC-MVP-10 适配层 Fake 切换 | URS-ADP-001/003/004, URS-ROB-001 | 集成 | |
| TC-MVP-11 **电梯技能 Fake 编排**（ElevatorAdapter） | URS-ROB-007 | E2E | Fake 不可豁免 |
| TC-MVP-12 **简单互斥**（点位/电梯/充电桩资源锁） | URS-SCH-003 | 仿真/集成 | |
| TC-MVP-13a 默认 `e_sign=false` 主流程无阻塞 | URS-AUD-004 | 集成 | 出厂配置断言 |
| TC-MVP-13b 开签名改限值被拦截直至批准 | URS-AUD-002 | 集成 | |
| TC-MVP-13c 批准通过后动作生效；驳回/过期不生效 | URS-AUD-002 | 集成 | |
| TC-MVP-14 Gateway 操作/数据/设置分组可达 | URS-API-003/004 | 集成 | |
| TC-MVP-15 适配层直连仪表（MVP） | URS-INS-008 | 集成 | |
| TC-MVP-16 地图载入与位姿刷新可视化 | URS-SCH-004/005 | E2E | PLN-002 |
| TC-MVP-17 实时/历史趋势看板 | URS-DAT-002 | E2E | |
| TC-MVP-18 会话断线事件与重连/任务失败策略 | URS-ROB-005 | 仿真/集成 | |
| TC-MVP-19 急停注入 → 任务中断/失败可测 | URS-ROB-009 | 仿真 | Fake 注入 |
| TC-MVP-20 报警历史查询与 CSV 导出 | URS-ALM-003 | 集成 | |
| TC-MVP-21 审计记录只追加（普通用户不可删） | URS-AUD-003 | 集成 | Should；可书面豁免须显式 |
| TC-MVP-22 Vue 核心路径 E2E（登录→任务→看板→报警） | URS-CLI-001 | E2E | |
| TC-MVP-23 杀进程后任务状态恢复或不明确失败 | URS-NFR-002 | 集成/手工 | |
| TC-MVP-24 组合/集群报告汇总（Should） | URS-RPT-002 | E2E | 可书面豁免须显式 |
| TC-EXT-03 边端代理+端侧缓存续传（演进） | URS-INS-009 | 扩展 | |
| TC-HIL-01 用户 AMR+仪表联调 | URS-ROB-002/004, URS-INS-001..003 | HIL | 并行门禁 |
| TC-HIL-02 充电状态与回充技能 | URS-ROB-003 | HIL | |
| TC-HIL-03 电梯真机联调（依赖用户设备） | URS-ROB-007 | HIL | 真机可豁免 |
| TC-EXT-01 浮游菌适配扩展 | URS-INS-006 | 扩展 | |
| TC-EXT-02 交通管制增强 | URS-SCH-006 | 扩展 | |
| TC-FUT-01 臂技能 Fake/联调 | URS-ROB-012 | PoC | |

### 6.4 质量门禁（MVP）

- 软件 Must 级 URS 对应用例通过或有书面豁免（电梯真机可豁免，**电梯 Fake 不可豁免**）。
- CI 绿：单元 + 集成 + Fake 冒烟（含电梯路径）。
- Gateway、批准流（签名开）、简单互斥用例通过。
- HIL 不阻塞软件 MVP 冻结；通过后记入 M6。
- **DoD（对齐 testing_quality.md，PLN-006）**：lint/typecheck 通过；相关单测通过；OpenAPI/配置 schema 已更新；无密钥入库（diff 扫描）；契约文档随变更更新。

---

## 7. 风险与缓解（软件侧）

| 风险 | 影响 | 缓解 |
|------|------|------|
| 用户设备/电梯 API 延期或不完整 | 真机联调推迟 | Fake 主路径（含电梯）；契约先行；录制回放适配器；仅移动 M6 |
| 未来切边端代理 | 续传与部署形态变化 | MVP 锁定直连；接口预留 via_edge_agent；边端须端侧缓存 |
| 前端框架已锁定 Vue | UI 技术选型已闭环 | TypeScript + Vue，按 Vue Web（MVP）实施 |
| 范围蔓延（清洁/硬件选型/臂） | 资源被抽走 | 严格上位机范围；臂走远期软件接口 |
| 合规期望过高 | 认证范围爆炸 | 「取向+开关」；开启签名强制批准流；非证书 |
| 多机冲突 | 调度复杂度 | **MVP 已定简单互斥**；增强单列演进 |
| **plan/scheme 文档漂移**（PLN-010） | 排期/门禁误读 | 里程碑以 plan §1.2 为唯一权威；里程碑结束核对 scheme §9 |
| **TBD 永久化**（时序库/PDF 等） | 验收悬空 | TBD 超期未关则升级为 `ref/risks.md` / issues |

---

## 8. 下一步立即行动（软件侧）

1. **按已锁定的 Vue（TypeScript + Vue）实施**并拉起 monorepo 骨架（目录以 scheme §4.2 为准）。
2. **产出 API Gateway / OpenAPI 草图**（常规操作、数据获取、设置类；见 DS 最小 API 资源表）。
3. **冻结适配器接口草案**（Amr/Particle/Climate/Airflow/**Elevator** + Fake）与 `devices.example.yaml`（含 `elevators[]`；`access_mode: direct`）。
4. **起草编排状态机**（调度调用 ElevatorAdapter；简单互斥资源锁；失败/重试）并配 Fake E2E 冒烟。
5. **起草批准流与签名开关设计**（默认 `e_sign=false`；开启强制批准流）及 TC-MVP-13a/b/c。
6. **维护跟踪文档（PLN-004）**：初始化/更新 `ref/progress.md`、`ref/tasks.md`、`ref/risks.md`；**每个里程碑结束更新 progress**；验收记录写入 `doc/test.md`。

> 开放决策已关闭（签名/Gateway/直连拓扑/电梯/互斥/Vue）；见 `urs.md` §7 / `progress.md`。

---

## 9. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V0.1 | 2026-09-25 | 初稿，含测试方案与 URS 映射 |
| V0.2 | 2026-09-25 | WBS/里程碑改为上位机；去掉选型/改装；测试以 Fake 为主 |
| V0.2.1 | 2026-09-25 | 用户确认前端锁定 Vue |
| V0.3 | 2026-09-25 | 写入 Gateway、电梯 MVP、批准流、简单互斥 |
| V0.4 | 2026-09-25 | 响应 `review_plan_260925`：声明里程碑权威；相对工期；TC-MVP-16+；P0a/b/c；DoD；签名用例拆分；Vue 页面清单；progress/tasks/risks；文档漂移风险；`doc/test.md` |
