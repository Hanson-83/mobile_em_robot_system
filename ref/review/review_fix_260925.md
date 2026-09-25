# 整改独立复核（Reviewer_Fix）

## 结论

**整改成立。**

本次实际核对当前工作区代码及测试，并以 `backend/.venv/bin/pytest` 运行：

```text
backend/tests/test_m1_contract.py
backend/tests/test_m2_scheduler.py
backend/tests/test_m3_compliance.py
```

结果为 **26 passed**。另以临时 `TestClient` 实测：先完成 WebSocket topics 订阅，再通过 HTTP 补传 measurement，已在同一连接收到后续 measurement 事件，确认不是仅回放一次。此前各项 P0 均已具备代码修复与相应测试证据；本复核未发现仍存 P0。

## 符合项

| 原问题 | 复核证据 |
|---|---|
| M2-001 / M4-001 报告超限关联 | `backend/app/services/reports.py:16-29` 先取任务测量记录 ID 集合，再以 `alarm.object_ref == task_id` 或属于该测量 ID 集合关联报警；`backend/tests/test_m2_scheduler.py:64-68` 断言报告 `summary.breach_count >= 1`，并验证 HTML 含超限指标。 |
| M3-001 用户组角色与权限配置 | `backend/app/adapters/repository.py:99-110` 将所属组的 `role_name` 纳入 `roles_for_user`；`backend/app/api/routes.py:665-677` 提供 `PATCH /roles/{role_name}`；`backend/tests/test_m3_compliance.py:143-173` 分别验证组成员获得 operator 权限及 viewer 角色权限可经 PATCH 配置后生效。 |
| M3-002 自动备份 | `backend/app/main.py:61-64` 启动时调用 `maybe_auto_backup`；`backend/app/services/backup.py:64-79` 按 `auto_backup_interval_minutes` 开关及上次执行时间判断；`backend/app/services/support.py:27,46` 声明并默认配置该间隔。 |
| M3-003 报告批准与关闭审计 | `backend/app/api/routes.py:452-465,798-819` 直接报告批准经 `_mark_report` 写入 `report.approve` 审计；`:610-623` 在关闭 `audit_trail` 前写入 `features.update` 审计；`backend/tests/test_m3_compliance.py:177-193` 覆盖并断言两项审计记录。 |
| M3-004 活动配置恢复路径 | `backend/app/services/backup.py:46-56` 将活动配置绝对路径写入 manifest；`:95-100` 恢复时按 manifest 中的 `devices_config`、`features_config` 目标写回；`backend/tests/test_m3_compliance.py:196-211` 使用非 `config_dir` 的自定义活动 YAML 验证恢复。 |
| M3-006 批准、签名与生效的事务性 | `backend/app/adapters/repository.py:682-716` 的 `commit_decision` 在同一 session 中更新批准状态、写电子签名、调用限值/报告领域变更，并只执行一次 `session.commit()`；`backend/app/api/routes.py:746-775` 将限值和报告批准生效逻辑作为该事务的 `apply` 回调传入。 |
| M1-003 无效 Bearer 限流 | `backend/app/main.py:159-172` 仅对已验证会话/API Token 分主体桶；无效 Bearer 回落 `ip:{host}`；`backend/tests/test_m1_contract.py:121-132` 用三个随机 Bearer 验证第三次请求返回 429。 |
| M1-004 / M4-002 WebSocket 持续订阅及地图订阅 | `backend/app/services/support.py:95-123` 维护订阅队列并在 `publish` 时投递；`backend/app/api/routes.py:854-888` 在订阅、回放后持续从队列发送事件并发送心跳；`frontend/src/views/MapView.vue:50-60` 建连后发送 topics 订阅且收到事件后刷新；`backend/tests/test_m2_scheduler.py:157-164` 覆盖订阅与事件接收。 |
| M2-002 等待语义 | `backend/app/services/scheduler.py:300-308` 的 `wait` 技能读取 `seconds` 并调用 `time.sleep(seconds)`。 |
| M2-007 补传限值评估 | `backend/app/api/routes.py:395-402` 对非幂等回放补传调用 `runtime.scheduler.evaluate_measurement(measurement)`；`backend/app/services/scheduler.py:413-443` 复用限值判断并生成 `limit.*` 报警。 |

## 仍存在的 P0

无。

## 复核边界

未将「省略 Created/Dispatched」判为 P0；其属于已说明的 MVP 简化，非本次复核的阻塞项。
