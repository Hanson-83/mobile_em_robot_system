# 技术说明 — 移动环境监测上位机

| 项 | 内容 |
|----|------|
| 日期 | 2026-09-25 |
| 范围 | M1–M4 软件主路径（Fake）。不含真机联调 |

## 1. 结构

单体模块化。对外只有 API Gateway（`/api/v1` 与 `/health`、`/ready`）。对内由 `AdapterFactory` 按 YAML 装配 AMR、仪表、电梯。电梯不挂在 AMR 适配器上。

调度在技能执行前按固定顺序加锁：区域 → 电梯 → 充电桩 → 点位。冲突默认排队，可改为立即失败。

电子签名默认关闭。打开后，修改限值和批准报告只创建 `ApprovalRequest`，审批通过并完成口令签名后才落库。

## 2. 运行与配置

- 设备：`config/devices.example.yaml`（`MER_DEVICES_CONFIG`）
- 开关：`config/features.example.yaml`（运行中修改写入数据库 `app_kv`，覆盖文件）
- 数据库：`MER_DATABASE_URL`。开发默认 SQLite `var/mer.db`。生产可改为 PostgreSQL，并安装 `uv sync --extra postgres`
- 密钥：`MER_SECRET_KEY`。默认值仅允许在 `MER_ALLOW_DEV_SECRET=true` 时通过就绪检查

切换真实设备时只改 YAML 的 `adapter` 字段。`amr_vendor_x`、`elevator_vendor_x` 以及仪表厂商类型目前会拒绝连接并保持离线，等待用户 API 文档后再实现。`amr_recorded` 可回放 JSON，用于没有真机时的契约演练。

## 3. 任务语义

- 创建任务只入队（状态直接是 `Queued`，MVP 不单独停留在 Created / Dispatched）。`POST /api/v1/scheduler/drain` 才驱动 Fake 执行。Web「下发并执行」会连续调用这两步。
- `wait` 技能按 `params.seconds` 阻塞当前调度步进。
- 未给技能列表时，默认：导航 → 粒子采样 → 温湿度 → 风速。
- 电梯用技能 `elevator_transfer`（Call → 可选导航到入口点 → Enter → Exit）。
- 低电量（默认 20%）会在导航前插入回充。
- 急停 / 故障 / 离线：在途任务失败。断线默认不恢复原任务，恢复在线后可下发新任务。
- 进程重启时，`Running` / `Dispatched` 记为失败，原因 `PROCESS_RESTART`；`Queued` 保留。

## 4. 数据

测量幂等键优先用调用方的 `client_request_id`，否则为 `sha1(device_id|sample_id|ts)`。重复上报保留第一次的值。

读数失败时适配层最多 3 次。重试后成功记 `uncertain`，最终失败记 `quality=bad` 并令任务失败。

报告先写 HTML。超限段按该任务的测量 ID 关联 `limit.*` 报警。PDF 引擎未选。

登录权限 = 用户角色 ∪ 所属用户组绑定的角色。改角色或组成员后，已有会话要重新登录才生效。

## 5. 备份

应用内备份复制 SQLite 文件、当前活动设备/开关 YAML（路径写入 `manifest.json`）和报告目录。恢复按清单写回活动路径，并重建数据库连接。`auto_backup_interval_minutes` 默认 60，启动时若到期会自动做一次；0 表示关闭。PostgreSQL 请按 `deploy/sql/backup_postgres.md` 使用 `pg_dump`。审计表在 SQLite 上有禁止 UPDATE/DELETE 的触发器；PostgreSQL 用 `deploy/sql/audit_append_only.sql`。

## 6. 迁移注意

- 不要把 `var/`、`.env`、真实 Token 提交入库。
- 修改权限码或 OpenAPI 路径时，同步前端与 `backend/openapi/openapi.json`。
- 新增仪表：加适配器类并在 `AdapterFactory` 注册，不改调度技能解释之外的业务分支；采样技能仍通过 `kind` 找仪表。
