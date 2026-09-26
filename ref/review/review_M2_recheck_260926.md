# M2 调度 MVP P1 复审意见（2026-09-26）

## 1. 审核元信息

| 项 | 内容 |
|----|------|
| 审核对象 | M2 P1 整改复审（对照 `ref/review/review_M2_260926.md` 的 M2-001、M2-002、M2-003） |
| 仓库 / 分支 | `/workspace` / `cursor/m2-scheduler-fake-8317` |
| 初审提交 | `9e40f82` — `feat(m2): 调度状态机、排队互斥与 Fake 全链路` |
| 整改提交 | `2a6f4e4` — `fix(m2): 锁顺序、失败策略与排队超时` |
| 复审时 HEAD | `e4561d4` — `docs(m2): 记录审核整改与排队超时决定` |
| 审核依据 | 初审意见；`ref/review/remediation_M2_260926.md`；`ref/project_scheme.md` §5.1；`doc/spec/ds.md` §6.1；`ref/decisions_260926.md` |
| 抽查范围 | `backend/app/services/mutex.py`、`backend/app/services/scheduler.py`、`backend/app/core/config.py`、`backend/app/api/routes/tasks.py`、`backend/tests/test_mutex.py`、`backend/tests/test_m2_scheduler.py` |
| 审核人 | **Reviewer_Gate** |
| 审核日期 | 2026-09-26 |
| 总体结论 | **通过** |

结论说明：初审三条 P1 均已在当前代码关闭。调度按 zone → elevator → charger → point 取锁，`MutexService` 拒绝同一持有者的逆序嵌套；`on_conflict=fail` 时冲突任务进入 `Failed` 并带 `CONFLICT_MUTEX`；排队自首次冲突起超过 `mutex_wait_s`（默认 30s）后，在下一次 `pump` 迁入 `Failed`。`cd /workspace/backend && .venv/bin/pytest -q` 为 30 passed，1 warning（Starlette/anyio 弃用警告）。

本复审未改业务代码、未 commit。P2（M2-004 起）不作为本次通过条件，只在与 P1 交界处记残留。

## 2. 验证结果

| 检查 | 结果 |
|------|------|
| `cd /workspace/backend && .venv/bin/pytest -q` | **通过**：30 passed，1 warning |
| M2-001 逆序 | `test_lock_order_rejects_elevator_after_point`：已持 `point` 再取 `elevator` 为 `VALIDATION_ERROR` |
| M2-001 调度顺序 | `_try_run` 固定四元组顺序；`test_zone_then_point_lock_order` 带 `zone_id`+`point_id` 到达 `Succeeded` |
| M2-002 | `test_fail_policy_marks_task_failed`：`on_conflict=fail` 且点位被占时，创建结果为 `Failed`，`error.code=CONFLICT_MUTEX` |
| M2-003 | `FeaturesConfig.mutex_wait_s` 默认 `30.0`；`test_queue_wait_timeout` 把 `queued_at` 拨到过去后 `/start` 得到 `Failed`，文案含「超时」 |
| 默认排队未回退 | `test_queue_then_start` 仍为冲突保持 `Queued`，释放后 `/start` 为 `Succeeded` |

## 3. 逐条复审

| ID | 原级别 | 复审结论 | 验证要点 |
|----|--------|----------|----------|
| M2-001 | P1 | **已关闭** | `LOCK_ORDER = (zone, elevator, charger, point)`。`try_acquire` 在占用成功前比较该 holder 已持类型的最高序号，新类型序号更小则拒绝。`_try_run` 只按该顺序对非空的 `zone_id` / `elevator_id` / `charger_id` / `point_id` 加锁；冲突或失败时 `_release_held` 释放本轮已持有的类型。任务创建模型已接收 `zone_id`、`charger_id`。 |
| M2-002 | P1 | **已关闭** | `fail` 时 `try_acquire` 仍抛 `CONFLICT_MUTEX`。`_try_run` 在状态仍为 `Queued` 时捕获该码，经 `_fail_queue` 迁到 `Failed`，写入 `error`（`code=CONFLICT_MUTEX`，`retryable=true`），清空 `queue_reason` 并落库，不再把异常抛回 API。`submit` 返回任务体，客户端看到终态而不是「HTTP 失败、列表仍排队」。 |
| M2-003 | P1 | **已关闭** | 首次抢锁失败时 `setdefault("queued_at", time.time())`。再次进入 `_try_run` 时若 `time.time() - queued_at > mutex_wait_s`，则 `_fail_queue(..., "排队等待超时")`。默认 30s 来自 `FeaturesConfig`，`decisions_260926.md` 已写明「等待超过 30s 记失败」。无后台计时器，超时在下一次 `pump`（`submit` / `start`）判定；这与初审已拆出的 P2 M2-004 一致，不把 M2-003 重新打开。 |

## 4. 残留（不恢复为 P1，不挡 M3）

| ID | 级别 | 位置 | 说明 |
|----|------|------|------|
| M2-R01 | P2 | `mutex.py` `release` / `_holder_types` | 同一 holder、同一类型的多把锁只记一次类型；释放其中一把就从顺序账本删掉该类型，另一把仍占用时可以再取更靠前的类型。TTL 过期只删 `_locks`，不回收 `_holder_types`，过期后同一 holder 可能被误拒。M2 调度每任务每类型至多一把，并在终态路径释放，当前用例打不到这两条。 |
| M2-R02 | P2 | `scheduler.py` `stop` → `_release` | `stop`/`cancel` 只释放电梯和点位，不释放 zone/charger。同步执行时 `_try_run` 的 `finally` 仍会用 `held` 释放全部；若取消发生在这条 `finally` 之外，zone/charger 会留到 TTL。 |
| M2-R03 | P2 | `test_m2_scheduler.py` | `test_zone_then_point_lock_order` 只断言 `Succeeded`，未观察加锁次序，也未覆盖 `charger_id`。`test_queue_wait_timeout` 用 `queued_at=1.0` 加 `/start`，未锁死「默认 30s」和「未超时仍 Queued」。`config/features.example.yaml` 未写出 `mutex_wait_s`，运行时缺省仍是模型默认 30。 |
| 初审 P2 | P2 | 见初审 M2-004–M2-011 | 本次不复审其关闭状态。M2-006 的 fail 端到端已有 `test_fail_policy_marks_task_failed`；双任务同点「A 跑完 B 再成功」仍未见。无后台 tick（M2-004）仍在：超过 30s 的排队任务会一直显示 `Queued`，直到有人 `submit`/`start` 触发 `pump` 才变成 `Failed`。 |

## 5. 与文档一致性

| 文档 | 复审结论 |
|------|----------|
| `ref/project_scheme.md` §5.1 | 锁顺序、`fail` 立即失败、等待超时 30s 与当前实现一致。等待超时在下次调度判定，不在满 30s 的时刻自行改状态。 |
| `doc/spec/ds.md` §6.1 | `Queued → Failed`（互斥 fail / 超时）已接通。超时与 fail 共用 `CONFLICT_MUTEX`。 |
| `ref/decisions_260926.md` | 与整改后的 `on_conflict`、`mutex_wait_s=30`、锁顺序一致。 |

## 6. 结论与 M3 门禁

- **总体结论：通过。**
- **剩余 P0：无。**
- **剩余 P1：无。** M2-001、M2-002、M2-003 关闭。
- **是否仍阻塞进入 M3：否。** 初审门禁是 P1 闭环或书面豁免；三条均已在代码中闭环，决策记录已同步。M2-R01–R03 与初审 P2 可随 M3 并行，不单独挡 M3。
