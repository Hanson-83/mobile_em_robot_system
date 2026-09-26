# M2 审核整改说明（2026-09-26）

| 项 | 内容 |
|----|------|
| 依据 | `ref/review/review_M2_260926.md` |
| 作者 | PM_Max |

| ID | 处理 |
|----|------|
| M2-001 | 调度按 zone → elevator → charger → point 取锁；`MutexService` 拒绝逆序嵌套 |
| M2-002 | `on_conflict=fail` 时任务迁到 Failed，不再停在 Queued |
| M2-003 | 排队超过 `mutex_wait_s`（默认 30s）迁到 Failed |

pytest：30 passed。P2（断言强度、limits API 与运行时不一致）留到 M3 前补齐，不阻塞本轮 M2 闭环。
