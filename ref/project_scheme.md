# 技术方案 — 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 文档编号 | MER-SCHEME-001 |
| 版本 | V0.4 |
| 日期 | 2026-09-25 |
| 作者 | PM_Max |
| 状态 | Draft |
| 范围 | **上位机技术方案**；硬件为外部系统与集成假设 |
| 依据 | `ref/requirement.md`、`doc/spec/urs.md` V0.3、`doc/spec/ds.md` V0.4 |
| 说明 | 技术正文；由 `ref/plan.md` 引用 |
| 权威声明 | **里程碑以 `ref/plan.md` §1.2 为准**（§9 与之逐字对齐）；**仓库目录以本文 §4.2 为权威布局** |

---

## 1. 总体方案与分期

### 1.1 定位

构建「**上位机自研**」的移动环境监测中控软件：编排调度用户选定的 AMR/仪表完成到点采样，提供数据持久化、看板、报警、批报告、权限与可开关合规能力（签名开启则批准流），并经 **API Gateway** 对外服务 MES/SCADA/DCS 与前端 App。

**明确不做**：

- 吸尘/拖地等清洁功能。
- **硬件设备选型与采购**（AMR、仪表、充电桩、电梯改造、机械臂、采样机构、网络基建）— 由用户负责。
- 本方案不输出选型清单或改装 BOM。

### 1.2 分期（软件交付物）

| 阶段 | 软件交付物 | 外部依赖（用户） |
|------|------------|------------------|
| MVP | 适配层 + Fake（含 **ElevatorFake**）；调度编排 + **简单互斥**（含电梯资源锁）；数据看板；报警；批报告；RBAC；审计/签名开关（开则批准流）；备份；**API Gateway** + OpenAPI；Vue Web | 用户提供设备 API/仿真或后续真机联调窗口；电梯硬件就绪后真机联调 |
| 扩展 | 浮游菌等适配契约；编排增强；桌面/移动；交通管制增强 | 用户扩展仪表就绪 |
| 远期 | 臂/深度相机技能与适配接口；更优多机算法 | 用户臂硬件与 API |

### 1.3 架构一句话

单体模块化上位机（Python FastAPI + TypeScript + Vue）经 **API Gateway** 对外、经**设备适配层**对内**直连** AMR/仪表（MVP）；**电梯经独立 ElevatorAdapter**；未来可扩展边端代理（须端侧缓存）；配置 YAML；合规能力可开关；开发以 Fake 为主路径（含电梯）。

**前端选型已锁定：Vue 3 + TypeScript + Vite，交付形态为 Vue Web（MVP）；本项目覆盖默认规范中的前端选型（不修改 `spec/tech_stack.md` 全局默认）。**

---

## 2. 外部系统与集成假设

> 本章替代原「AMR 选型与改装」「仪表型号对照」章节。仅描述上位机集成所需假设，**非选型结论**。

### 2.1 用户负责的外部系统

| 外部系统 | 用户职责 | 上位机侧期望 |
|----------|----------|--------------|
| AMR | 选型、商务、改装、充电桩、洁净材质 | 文档化 API：导航、状态、充电、地图/点位同步（**不含**电梯方法；电梯走 ElevatorAdapter） |
| 粒子/温湿度/风速等 | 选型、采购、安装供电、**独立联网（MVP 直连）** | 可远程启停/读数或等价协议；参数进 YAML；MVP 直连适配层 |
| 电梯/楼控 | **硬件改造与品牌由用户负责** | 上位机经 **ElevatorAdapter** 提供 Call/Enter/Exit 技能 + ElevatorFake；真机联调依赖用户设备就绪 |
| 现场网络 | WiFi/VLAN/隔离 | 可达性；软件侧超时与续传 |
| 协作臂（远期） | 选型与安装 | Arm/Camera API 供适配 |

### 2.2 对内拓扑（直连 MVP / 边端演进）— 已决议

| 概念 | 通俗说明 |
|------|----------|
| 直连（**MVP/现在**） | 仪表（及适用设备）独立联网，由上位机**适配层直接通讯**，**不上边端代理** |
| 边端（**未来考虑**） | 机器人本体/车载工控上的**代理软件**；若启用，**必须**能做端侧数据缓存 |
| API Gateway | **对外**统一入口（与对内适配层区分） |
| ElevatorAdapter | **独立适配器**；调度编排调用其技能；**不**挂在 AmrAdapter 上 |

**决议**：MVP 实现与验收以**直连**为准。演进路径：直连 → 可选边端代理（含端侧缓存）。适配层接口预留未来代理模式；**两种模式不对等默认**。

### 2.3 集成契约（软件）

- 适配器接口见 `doc/spec/ds.md` §4.1（AmrAdapter **不含**电梯方法；ElevatorAdapter 独立）。
- 配置 schema：`robots[]` / `instruments[]` / **`elevators[]`** / `features{}`；MVP `access_mode: direct`；预留 `via_edge_agent`。
- 错误模型与坐标系/单位约定在适配边界统一。
- Fake/Simulator 与真实适配器实现同一接口（含 ElevatorFake）。

### 2.4 他厂参考（仅上位机可借鉴）

可借鉴思路：**任务流程编排、数据上抛与看板呈现、报警与批报告形态**。

**删除/不采用**：引导本项目做清洁机；将他厂硬件参数/型号作为本项目选型结论；改装 BOM 照搬。

---

## 3. 监测数据与采样命令（软件）

### 3.1 原则

- 通讯与型号差异收敛在适配层 + YAML。
- 每种仪表：真实适配器（用户文档就绪后）+ Fake。
- 点位绑定 instrument profile 与限值；超限复测可作为组合任务模板。

### 3.2 MVP 数据域

| 指标 | 领域命令 | 配置占位 |
|------|----------|----------|
| 粒子 | start/stop/read_channels | adapter_type, access_mode=direct, endpoint/port, channel_defs |
| 温湿度 | read_temp_humidity | adapter_type, access_mode=direct, unit, precision |
| 风速 | read_air_speed | adapter_type, access_mode=direct, unit |

扩展：浮游菌参数（时长/流量等）配置化。

### 3.3 Measurement quality（SCH-011）

| quality | 含义 | 落库策略 |
|---------|------|----------|
| `good` | 有效采样 | 正常写入 Measurement |
| `uncertain` | 可疑（超时重试后成功等） | 写入并标记 |
| `bad` | 采样失败/无效值 | **默认落数带 quality=bad**（保留失败痕迹，供审计）；看板默认过滤 bad |
| `missing` | 未采到（任务跳过点） | 可不落数或落 missing（配置项 `measurement.write_missing`，默认 false） |

---

## 4. 上位机软件方案

### 4.1 模块

见 `doc/spec/ds.md`：API Gateway、调度、数据、报警、报表、鉴权、批准流、适配层（含 **ElevatorAdapter**）、审计/签名、备份、前端。

### 4.2 推荐模块目录（单体仓库）— **目录权威（SCH-007）**

> **声明**：本文 §4.2 为仓库**权威布局**；`doc/spec/ds.md` 须引用本节约定，**不得**再使用顶层独立 `adapters/` 目录。

```text
mobile_em_robot_system/
  backend/
    app/
      api/           # Gateway 路由 / OpenAPI（operations/data/settings）
      domain/        # 任务、点位、报警、批准流等领域
      adapters/      # AMR/仪表/电梯/仓储实现（含 fake/）；ElevatorAdapter 在此
      services/      # 调度、报表、备份、资源锁
      core/          # 配置、安全、错误模型、可观测性
    tests/
    pyproject.toml   # uv
  frontend/
    src/             # Vue Web → 仅调 Gateway
  config/
    devices.example.yaml
    features.example.yaml
  doc/
  ref/
  spec/
  deploy/
    docker-compose.yml
    .env.example
```

### 4.3 适配层（对内）与 API Gateway（对外）

- `AdapterFactory` 按 `type` 装配；MVP `access_mode=direct`；预留未来 `via_edge_agent`。
- **ElevatorAdapter**（`elevator_fake` / `elevator_vendor_x`）独立注册；调度技能 `call_elevator` / `enter_elevator` / `exit_elevator` **只**调用 ElevatorAdapter。
- 统一生命周期：`start/stop/health`。
- 遥测归一化为领域 DTO。
- Gateway：鉴权、限流、OpenAPI；首批对接 MES/SCADA/DCS 与 Vue Web。
- 集成测试：Gateway + 领域服务 + 适配层 Fake（含电梯）。

#### 4.3.1 Gateway 鉴权 / 限流 / 权限映射（SCH-006）

| 项 | MVP 约定 |
|----|----------|
| Token 模型 | `Authorization: Bearer <access_token>`；服务账号可用长期 **API Token**（`api_client` 角色） |
| 限流默认 | 每 Token **60 req/min**（可配置 `gateway.rate_limit_per_min`）；超限返回 `429 RATE_LIMITED` |
| 权限码映射 | `operations.*` → 任务/调度操作；`data.*` → 查询/导出；`settings.*` → 限值/用户/开关；见 DS §4.2 资源表 |
| 版本策略 | 破坏性变更走 `/api/v2`；兼容变更保留 v1 + OpenAPI changelog |

### 4.4 配置示例（示意）

```yaml
# config/devices.example.yaml
robots:
  - id: robot-01
    adapter: amr_fake   # 用户就绪后改为 amr_vendor_x 等
    endpoint: "http://192.168.x.x/api"
    # model: "<user-provided>"
instruments:
  - id: pc-01
    robot_id: robot-01
    adapter: particle_fake
    access_mode: direct      # MVP：直连；未来可 via_edge_agent（须端侧缓存）
    # model: "<user-provided>"
elevators:
  - id: elev-01
    adapter: elevator_fake   # 或 elevator_vendor_x
    endpoint: "http://192.168.y.y/api"
    floors: [1, 2, 3]
    # model: "<user-provided>"
features:
  audit_trail: false
  e_sign: false              # 建议默认关闭；开启则强制批准流
  elevator_skills: true      # MVP 纳入；Fake 验收；真机依赖用户
  resource_mutex: simple     # MVP 简单互斥
  realtime_channel: websocket  # 锁定 WebSocket；SSE 为扩展
```

---

## 5. 地图 / 点位 / 调度（软件）

1. **地图**：导入或同步用户 AMR 厂工具产出的地图/等价表示；上位机显示层标准化。
2. **点位**：地图标注；JSON/YAML 导入导出；任务引用。
3. **调度**：
   - MVP：单机队列 + 多机并行 + **简单互斥**（资源锁：点位 / **电梯** / 充电桩、区域互斥）。
   - **演进**：扩展阶段增强交通管制；远期更优算法（见 URS-SCH-006 / DS §6）。
4. **电梯**：调度编排调用 **ElevatorAdapter** 技能（Call/Enter/Exit）；硬件/品牌用户负责；真机联调依赖用户设备就绪。
5. **充电**：电量阈值触发 `DockCharge`（依赖状态字段由 AmrAdapter 提供）。

### 5.1 资源锁方案（SCH-003）

| 项 | 约定 |
|----|------|
| 资源类型 | `point` / `elevator` / `charger` / `zone`（可扩展） |
| 获取时机 | 技能执行前 `acquire(resource_type, resource_id, holder=task_id, ttl)` |
| 释放时机 | 技能成功/失败/取消后 `release`；进程崩溃依赖 TTL 过期 |
| 超时 | 默认 TTL **120s**（可配置）；获取等待超时默认 **30s** |
| 冲突策略 | `queue`（默认排队）或 `fail`（立即失败），配置 `resource_mutex.on_conflict` |
| 锁顺序（防死锁） | 固定顺序：**zone → elevator → charger → point**；嵌套获取必须按此序 |
| 与集群屏障 | 集群同步屏障**不**替代资源锁；屏障只协调任务阶段，资源仍须加锁 |

**2 机争用同一点位（伪流程）**：

```text
TaskA / Robot-01          LockService           TaskB / Robot-02
  | acquire(point,P1) --> |                       |
  | <OK holder=A          |                       |
  | navigate+sample       | <-- acquire(point,P1) |
  |                       | queue or fail(B)      |
  | release(P1) --------> |                       |
  |                       | --grant--> B          |
  |                       |                       | navigate+sample
```

电梯同理：`acquire(elevator, elev-01)` 后再调用 ElevatorAdapter。

---

## 6. 数据与看板

| 能力 | 方案要点 |
|------|----------|
| 实时 | **WebSocket** 推送测量与位姿（经 Gateway 受控通道）；SSE 列为扩展 |
| 历史 | 查询 API + 图表 |
| 限值 | 点位/全局规则；超限 → 报警；变更可走批准流（若签名开） |
| 导出 | **MVP 默认 CSV**（报警/数据）；Excel 可选扩展 |
| 报告 | **先 HTML 可归档**，再 PDF（库选型轻微 TBD；关闭条件：选定 weasyprint/chromium 之一） |
| 缓存续传 | 见 §6.1 |

看板区块：地图、机器人状态、当前任务、实时曲线、报警列表。

### 6.1 续传幂等与重试责任（SCH-004）

| 项 | MVP 约定 |
|----|----------|
| 拓扑 | **直连**；无边端队列 |
| 幂等键生成 | 采集管道/适配层生成 `idempotency_key`（规则见 DS：`device_id + sample_id + ts` 或 `client_request_id`） |
| Upsert | 数据服务按唯一约束 Upsert；重复上报 **忽略**（不覆盖 good→bad，除非显式修正 API） |
| 重试责任 | **适配层**负责设备读失败退避重试（上限 3 次，指数退避 1s/2s/4s）；领域服务负责入库冲突处理 |
| 边端补传 | 扩展（URS-INS-009）；接收侧仍用同一幂等键 |

### 6.2 Vue MVP 页面清单（附）

与 `plan.md` §3.1 一致：登录、地图监控、任务编排、点位/限值、实时趋势、报警、报告、用户权限、系统开关、批准中心。

---

## 7. 与他厂方案对比（上位机视角）

| 维度 | 他厂参考（仅思路） | 本系统（上位机） |
|------|--------------------|------------------|
| 产品形态 | 监测 + 清洁一体 | **仅环境监测软件**；不做清洁；不做硬件选型 |
| 软件 | 车载 APP + 服务器看板 | **上位机自研** FastAPI + Vue Web；**API Gateway** 对外 |
| 调度 | 偏单机 | **多机编排**、组合/集群；MVP 简单互斥（含电梯锁） |
| 集成 | 固定仪器 | **适配层**直连（MVP）+ Fake；**独立 ElevatorAdapter**；未来可选边端缓存 |
| 合规 | 未强调 | **审计/电子签名可开关**；开启进批准流 |

---

## 8. 环境与部署（服务器/客户端）

- **服务器**：Ubuntu LTS 优先；配置随并发评估（小规模参考值不写入承诺）。
- **运行**：`uv sync` + systemd 或 Docker Compose。
- **客户端**：现代浏览器（Vue Web）；桌面/移动分期；均经 API Gateway。
- **时间同步**：NTP。
- **备份**：PostgreSQL 业务库 + `config/` + 报告文件目录；作业可用 systemd timer/cron（频率试点后定）；演练对齐 TC-MVP-09。

### 8.1 部署安全清单（SCH-008）

| 项 | MVP 态度 |
|----|----------|
| `.env.example` | 仓库提供占位（无真实密钥）；实际密钥仅环境变量/密钥通道 |
| 禁止密钥入库 | CI/提交前扫描；违规阻断 |
| 默认鉴权 | **强制开启**；无匿名写操作 |
| TLS | **MVP 默认内网 HTTP + 强制鉴权**；TLS 按现场部署开启。采用明文 HTTP 时须**书面风险接受**（记入部署记录）；若客户要求则**强制 TLS** |
| 健康检查 | `GET /health`（存活）、`GET /ready`（依赖就绪）；容器/systemd 日志走 stdout JSON |

### 8.2 日志与健康检查（SCH-005）

- 结构化日志字段对齐 DS「可观测性」专节（ts/level/module/request_id/task_id/robot_id）。
- 禁止记录密钥与完整原始设备报文。
- 引用 `spec/observability.md`。

---

## 9. 里程碑对应的软件交付物

> **权威源**：里程碑 **ID 与名称**以 `ref/plan.md` §1.2 **逐字对齐**（SCH-001）。本表只补充「该里程碑的软件交付物」细节，不另立语义。

| ID | 里程碑 | 软件交付物 |
|----|--------|------------|
| M0 | 文档基线 | URS/DS/方案/计划（上位机范围 + 软件决策；V0.4 审核整改）评审通过 |
| M1 | 契约与骨架 | 适配接口草案（含 ElevatorAdapter）+ API Gateway/OpenAPI 草图 + 仓库骨架（§4.2）+ Fake 冒烟（含 ElevatorFake） |
| M2 | 调度 MVP | Fake 全链路：任务 → 模拟采样/电梯 → 看板/报警/报告；简单互斥（含电梯锁）可测 |
| M3 | 数据与合规 | 点位/限值/趋势、RBAC、审计/签名开关+批准流、备份恢复（PG+config/+报告目录） |
| M4 | Web MVP 冻结 | URS-MVP Must（软件项）测试通过；电梯以 Fake 验收；Vue 核心页面冻结；真机联调不阻塞冻结 |
| M5 | Gateway 与多端契约 | OpenAPI 稳定版；MES/SCADA/DCS 对接能力；桌面/移动可分期立项 |
| M6 | 联调门禁 | 用户提供设备/电梯 API 后的适配器联调通过（并行，依赖用户硬件/电梯就绪） |
| M7 | 扩展 / 远期 | 浮游菌适配；交通管制增强；臂技能接口 PoC（软件） |

---

## 10. 开放问题（上位机）

**暂无阻塞性开放问题。** 轻微 TBD：

1. 时序存储：MVP 用 PG 分区表；保留期/QPS 触发 Timescale（见 DS 决策门槛）。
2. 报告 PDF 引擎选型（HTML 归档已默认）；地图中间表示标准化、时区展示细则。
3. 桌面/移动技术选型（扩展阶段）。
4. 多机交通管制增强算法形态（扩展/远期）。
5. 密码策略/会话超时具体数值（配置项占位已在 DS）。

**已关闭（2026-09-25）**：电子签名开/关+批准流；API Gateway 与首批对接；对内拓扑 MVP 直连、边端演进（须端侧缓存）；电梯纳入 MVP（**独立 ElevatorAdapter**）；多机简单互斥及演进；前端 Vue；实时通道锁定 WebSocket；导出默认 CSV；里程碑权威=plan §1.2；目录权威=scheme §4.2。

硬件选型与供应商商务不在本方案开放问题内。

---

## 11. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V0.1 | 2026-09-25 | 初稿 |
| V0.2 | 2026-09-25 | 改为上位机技术方案；硬件章改为外部系统与集成假设 |
| V0.2.1 | 2026-09-25 | 用户确认前端锁定 Vue |
| V0.3 | 2026-09-25 | 写入 Gateway、直连、签名+批准流、电梯 MVP、简单互斥 |
| V0.4 | 2026-09-25 | 响应 `review_project_scheme_260925`：§9 按 plan 逐字对齐；elevators[] + ElevatorAdapter；资源锁；幂等；Gateway 限流/Token；可观测性/部署安全；目录权威；CSV/HTML；Measurement quality |
