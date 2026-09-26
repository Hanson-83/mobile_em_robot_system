# 操作日志

| 日期 | 操作者 | 操作摘要 | 路径/对象 | 备注 |
|------|--------|----------|-----------|------|
| 2026-09-25 | PM_Max | 根据 `ref/requirement.md` 与 `spec/*`、他厂参考材料，生成用户需求规范、设计规范、技术方案与项目规划；并写入进度摘要 | 见下方路径列表 | 文档阶段；未改业务源码；未 git clone/push |
| 2026-09-25 | PM_Max | **范围收窄为上位机**：备份四份核心文档后覆盖写 V0.2；更新本日志与 `ref/progress.md` | 见「范围收窄」节 | 硬件选型改由用户负责；不做清洁/不做硬件选型 |
| 2026-09-25 | PM_Max | **前端选型锁定 Vue**；更新六份文档并备份 | 见「前端选型锁定 Vue」节 | TypeScript + Vue；Vue Web MVP |
| 2026-09-25 | PM_Max | **软件决策写入 V0.3**：签名+批准流、API Gateway、对内拓扑 MVP 直连（边端演进）、电梯 MVP、简单互斥；备份六份后覆盖 | 见「软件决策写入」节 | 开放问题收敛为轻微 TBD；未改 tech_stack.md |
| 2026-09-25 | PM_Max | **审核整改 V0.4**：按 Reviewer_Max 三份意见升级 ds/project_scheme/plan；备份后写回；更新 progress/risks/tasks；写 remediation_note | 见「审核整改 V0.4」节 | P0：里程碑权威、ElevatorAdapter、附录 A；未改 tech_stack.md |

## 2026-09-25 生成路径列表

- `doc/spec/urs.md` — 用户需求规范（URS）
- `doc/spec/ds.md` — 设计规范（DS）
- `ref/project_scheme.md` — 技术方案
- `ref/plan.md` — 规划/计划（含测试方案，引用 project_scheme）
- `ref/progress.md` — 进度状态（文档阶段完成）
- `doc/operation_log.md` — 本操作日志（本条）

生成流程：先在构建机 `/workspace/mer_deliverables/` 撰写 → 拷贝至用户机临时目录 → `Copy-Item` 至项目根 `D:\Projects\mobile_em_robot_system\` 对应路径；验证 UTF-8 与文件存在。

## 2026-09-25 上位机范围收窄

### 变更原因

用户明确：所有硬件设备选型由用户自己做；本次任务与文档仅针对上位机（服务器+客户端）系统开发。

### 备份（同目录，AGENTS.md 命名）

- `doc/spec/urs.md_backup_20260925_上位机范围收窄_01.md`
- `doc/spec/ds.md_backup_20260925_上位机范围收窄_01.md`
- `ref/project_scheme.md_backup_20260925_上位机范围收窄_01.md`
- `ref/plan.md_backup_20260925_上位机范围收窄_01.md`

### 覆盖写回（V0.2）

- `doc/spec/urs.md`
- `doc/spec/ds.md`
- `ref/project_scheme.md`
- `ref/plan.md`
- `ref/progress.md`（更新）
- `doc/operation_log.md`（本追加）

### 流程

1. box `/workspace/mer_host_scope/` 生成新稿  
2. CopyFromBox → `C:\Users\heng.wang\AppData\Local\Temp\mer_host_scope\`  
3. 用户机 Shell：项目内 `Copy-Item` 备份四份核心稿 → 再覆盖新版  
4. UTF-8 无 BOM 校验  

### 风险与回滚

- 风险：覆盖写错范围表述。回滚：用上述 `_backup_20260925_上位机范围收窄_01` 文件 `Copy-Item` 还原。

## 2026-09-25 前端选型锁定 Vue

用户确认上位机前端锁定 **Vue（TypeScript + Vue）**。已更新：

- `doc/spec/ds.md`：技术栈、客户端、风险与修订记录
- `ref/project_scheme.md`：方案架构、Vue Web（MVP）与开放问题
- `ref/plan.md`：WBS、优先级、风险与立即行动
- `doc/spec/urs.md`：Vue Web（MVP）客户端表述与开放问题
- `ref/progress.md`：决策与剩余开放问题
- `doc/operation_log.md`：本次操作记录

修改前已备份上述六份实际改动文件，命名为同目录 `*_backup_20260925_锁定Vue_01.md`；写回文件为 UTF-8 无 BOM。

## 2026-09-25 软件决策写入（V0.3）

用户已确认多项上位机决策，写入 URS/DS/project_scheme/plan，并从开放问题移除。

### 已写入决策摘要

1. **电子签名**：可配置开/关；开启则强制批准流（与签名绑定）；**建议默认关闭**（建议非硬性）。
2. **对外 API**：须有 **API Gateway**；首批对接 MES/SCADA/DCS 等与前端 App（Vue Web 及后续客户端）；能力：常规操作、数据获取、设置类。
3. **对内拓扑**：**MVP/现在=直连**（仪表独立联网→适配层直接通讯，不上边端）；**未来**再考虑边端代理（须端侧数据缓存与断网续传）；接口预留；与 Gateway 区分。两种模式不对等默认。
4. **电梯**：联动技能+Fake **纳入 MVP 验收**；硬件/品牌用户负责；真机联调依赖用户设备就绪。
5. **多机冲突**：MVP **简单互斥**；演进路径写入 plan/ds。

### 备份（同目录）

- `doc/spec/urs.md_backup_20260925_软件决策写入_01.md`
- `doc/spec/ds.md_backup_20260925_软件决策写入_01.md`
- `ref/project_scheme.md_backup_20260925_软件决策写入_01.md`
- `ref/plan.md_backup_20260925_软件决策写入_01.md`
- `ref/progress.md_backup_20260925_软件决策写入_01.md`
- `doc/operation_log.md_backup_20260925_软件决策写入_01.md`

### 覆盖写回（V0.3）

- `doc/spec/urs.md`
- `doc/spec/ds.md`
- `ref/project_scheme.md`
- `ref/plan.md`
- `ref/progress.md`
- `doc/operation_log.md`（本追加）

### 流程

1. box `/workspace/mobile_em/out/` 生成新稿  
2. CopyFromBox → 用户机 Temp / Desktop xfer  
3. 用户机 Shell：项目内备份 → `Copy-Item` 覆盖  
4. UTF-8 无 BOM 校验  

### 风险与回滚

- 风险：决策表述与用户口头不一致。回滚：用上述 `_backup_20260925_软件决策写入_01` 文件还原。
- 未修改 `spec/tech_stack.md` 全局默认（仅在 DS/方案中引用并说明本项目覆盖前端选型）。

### 拓扑补充修正

用户补充：MVP 仅为直连，不上边端；边端为未来考虑且须端侧缓存。已修正 URS/DS/方案/计划/进度/本日志中「两种均可、MVP 默认」类表述。

| 2026-09-25 | PM_Max | **审核整改 V0.4**：按 Reviewer_Max 三份意见升级 ds/project_scheme/plan；备份后写回；更新 progress/risks/tasks/operation_log；写 remediation_note | 见「审核整改 V0.4」节 | P0：里程碑权威、ElevatorAdapter、附录 A；未改 tech_stack.md |

## 2026-09-25 审核整改 V0.4

### 变更原因

Reviewer_Max 对 ds / project_scheme / plan（V0.3）出具有条件通过意见；PM_Max 落实硬性整改升 V0.4。

### 备份（同目录）

- `doc/spec/ds.md_backup_20260925_审核整改V04_01.md`
- `ref/project_scheme.md_backup_20260925_审核整改V04_01.md`
- `ref/plan.md_backup_20260925_审核整改V04_01.md`
- （progress/operation_log 同步备份同前缀）

### 覆盖写回（V0.4）

- `doc/spec/ds.md`
- `ref/project_scheme.md`
- `ref/plan.md`
- `ref/progress.md`、`ref/risks.md`、`ref/tasks.md`（新建/更新）
- `doc/spec/review/remediation_note_260925.md`
- `ref/review/remediation_note_260925.md`
- `doc/operation_log.md`（本追加）

### 三项 P0 落点

1. 里程碑：`plan.md` §1.2 权威；`project_scheme.md` §9 逐字对齐；`ds.md` 文首声明  
2. 电梯：独立 ElevatorAdapter；YAML `elevators[]`；AmrAdapter 无电梯方法；三文一致  
3. 追溯：`ds.md` 附录 A 覆盖全部 MVP Must（45）

### 风险与回滚

- 回滚：用 `_backup_20260925_审核整改V04_01` 还原三份核心稿。
- 未修改 `spec/tech_stack.md`；未写入硬件选型。

| 2026-09-25 | PM_Max | **M1 开工**：仓库骨架、适配 Fake、Gateway 草图、Vue 壳、pytest；初始化 test.md；待确认清单 | 见「M1 契约与骨架」 | 未改 URS/DS 正文；真机未测 |

## 2026-09-25 M1 契约与骨架

### 操作

- 新建 `backend/`、`frontend/`、`config/`、`deploy/`（对齐 scheme §4.2）。
- 适配层 Protocol + Fake + VendorStub；Gateway FastAPI；Vue 登录/地图/任务壳。
- 初始化 `doc/test.md`、`doc/technical_manual.md`、`ref/pending_confirmations.md`。
- 备份：`ref/progress.md_backup_20260925_M1开工_01.md` 等。

### 风险与回滚

- 风险：占位 API 被误认为已完成业务。缓解：路由注明 placeholder；tasks.md 标部分完成。
- 回滚：丢弃本特性分支或还原备份文档。
- 开发账号口令仅本地；`MER_SECRET` 走环境变量。

| 2026-09-25 | PM_Max | **M1 审核整改**：统一错误体、去掉源码内置口令/占位密钥、强化 Fake 测试、任务列表、features 活配置 | 见 Reviewer_Code `review_M1_260925.md` | pytest 16 passed |

| 2026-09-26 | PM_Max | **M2 调度 MVP**：状态机、排队互斥、重连、Modbus 通道占位、报警与 HTML 报告；写入用户确认 | `backend/app/services/scheduler.py`；`ref/decisions_260926.md` | pytest 26 passed；未做真机 |

| 2026-09-26 | PM_Max | **M3 合规**：点位/限值、批准流、审计只追加、备份恢复、趋势查询 | `backend/app/services/compliance.py` `backup.py` | pytest 36 passed |

| 2026-09-26 | PM_Max | **M4 Vue 页面清单**：十个页面接通 Gateway；浏览器走通核心路径 | `frontend/src/views/` | 构建通过；报告改为任务下拉 |

| 2026-09-26 | PM_Max | **M5 Gateway 稳定版**：OpenAPI 1.0.0、MES 门面、API Token、契约测试 | `openapi_v1.stable.yaml`；`integrations.py`；`doc/mes_integration.md` | pytest 41 passed；桌面/移动分期 |

| 2026-09-26 | Reviewer_API | M5 初审有条件通过（P1×3） | `ref/review/review_M5_260926.md` | |

| 2026-09-26 | PM_Max | **M5 审核整改**：契约对齐、幂等、对称测试、realtime/WS/Token hardening | `remediation_M5_260926.md` | |

| 2026-09-26 | Reviewer_API_Recheck | M5 复审**通过**，建议冻结 OpenAPI 1.0.0 | `ref/review/review_M5_recheck_260926.md` | P0/P1=0 |

| 2026-09-26 | PM_Max | **补记经验教训**：M1–M5 审核整改中的坑此前大多只留在 review 文件，未回写 `doc/lession_learned.md`。备份后按可复用条目补齐 | `doc/lession_learned.md`；备份 `doc/lession_learned.md_backup_20260926_补记M1至M5_01.md` | 漏记，不是没有教训 |

## 2026-09-26 M5 Gateway / OpenAPI 稳定版

### 操作

- 分支：`cursor/m5-gateway-openapi-8317`（基于 `cursor/m4-vue-mvp-8317`）。
- 新增 `backend/app/api/openapi_v1.stable.yaml`、`/api/v1/integrations/mes/*`、`MER_API_TOKENS_JSON`。
- 文档：`doc/openapi_changelog.md`、`doc/mes_integration.md`；更新 progress/tasks/test。
- 测试：限流器各用例重置，避免跨测累加 429。

### 风险与回滚

- 风险：MES 门面与 `/api/v1/tasks` 双路径，需保持语义一致。缓解：共用 Scheduler/Store。
- 回滚：丢弃特性分支；草图文件仍保留作历史。

