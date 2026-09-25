# 测试与验证记录

| 项 | 内容 |
|----|------|
| 日期 | 2026-09-25 |
| 环境 | 本机 Python 3.12、Node 22；SQLite；无真机 |
| 命令 | `backend`: `uv run ruff check app tests && uv run pytest`；`frontend`: `npm run typecheck && npm run build` |
| 结果 | pytest 26 通过；ruff 通过；前端 `vue-tsc` 通过。生产构建在整改前已通过，整改后以类型检查为准 |
| 浏览器 | 2026-09-25 整改后复点：登录 admin → 地图（两台机器人与采样点）→ 系统开关（自动备份间隔 60、电子签名可见）→ 用户页（admin/operator/viewer）→ 批准中心空列表 → 报警页。早前另走过任务 Succeeded、点位、趋势、报告 |

真机 / HIL 不在本次执行范围，由用户在专用环境执行后回填。

## 用例记录

| 用例 | 结果 | 证据 |
|------|------|------|
| TC-MVP-01 点位与限值 | 通过 | `test_m2_scheduler.py`、`test_m3_compliance.py` |
| TC-MVP-02 Fake 单机全流程 | 通过 | `test_single_robot_sampling_report` |
| TC-MVP-03 超限报警确认 | 通过 | `test_limit_alarm_ack_close_and_csv` |
| TC-MVP-04 批报告 | 通过 | 超限任务报告 `breach_count>=1` 且 HTML 含指标；早前浏览器查看过 HTML |
| TC-MVP-05 断点续传幂等 | 通过 | `test_idempotent_ingest_and_websocket` |
| TC-MVP-06 RBAC | 通过 | `test_rbac_forbidden`；`test_group_role_grants_permission`；`test_role_permission_is_configurable` |
| TC-MVP-07 审计开关 | 通过 | `test_audit_append_only`；`test_report_approve_and_audit_switch_are_recorded` |
| TC-MVP-08 Gateway 鉴权与 OpenAPI | 通过 | `test_openapi_groups_and_health`；`backend/openapi/openapi.json` |
| TC-MVP-09 备份恢复 | 通过（SQLite） | `test_backup_restore_roundtrip`；启动自动备份与自定义 YAML 路径 `test_auto_backup_restores_active_yaml`。PostgreSQL 仍为手工 `pg_dump` |
| TC-MVP-10 Fake 切换 | 通过 | `test_factory_switches_fake_recorded_and_vendor` |
| TC-MVP-11 电梯 Fake | 通过 | `test_elevator_transfer_and_mutex` |
| TC-MVP-12 简单互斥 | 通过 | `fail` 见电梯测例；默认 `queue` 见 `test_queue_mutex_and_fault_disconnect_wait` |
| TC-MVP-13a/b/c 签名与批准 | 通过 | `test_approval_flow`、`test_approval_expired`、默认 `e_sign=false` |
| TC-MVP-14 Gateway 分组 | 通过 | OpenAPI tags：operations / data / settings |
| TC-MVP-15 直连 | 通过 | 配置 `access_mode: direct`，适配器字段可断言 |
| TC-MVP-16 地图与位姿 | 通过 | 单机流程断言位姿；浏览器地图页 |
| TC-MVP-17 趋势 | 通过 | 测量查询 API；浏览器趋势页 |
| TC-MVP-18 断线 | 通过 | 离线报警，以及 Running 任务 `DEVICE_OFFLINE`（`test_queue_mutex_and_fault_disconnect_wait`） |
| TC-MVP-19 急停 | 通过 | `error_code=ESTOP`；同文件另测 `FAULT` 与 `device.fault` |
| TC-MVP-20 报警 CSV | 通过 | `test_limit_alarm_ack_close_and_csv` |
| TC-MVP-21 审计只追加 | 通过 | DELETE 返回 405；SQLite 触发器拒绝 UPDATE（`test_audit_table_rejects_update`）。PostgreSQL 脚本见 `deploy/sql/audit_append_only.sql`，未在 PG 上执行 |
| TC-MVP-22 Vue 核心路径 | 通过 | 整改后浏览器复点登录、地图、开关、用户、批准中心、报警；早前已点任务、点位、趋势、报告 |
| TC-MVP-23 进程重启 | 通过 | `test_process_restart_marks_running_failed`，在途任务标 `PROCESS_RESTART` |
| TC-MVP-24 组合/集群报告 | 通过 | `test_composite_and_cluster_summary`。未做书面豁免 |
| TC-HIL-01/02/03 | 未执行 | 等待用户真机环境。不阻塞 Fake 主路径 |
| TC-EXT / TC-FUT | 未作为 MVP 门禁 | 浮游菌、臂、边端仅为占位 |

## 未覆盖

- 生产 PostgreSQL 的备份恢复演练
- TLS、多副本、长时间性能基线（URS-NFR-001）
- 厂商协议报文
