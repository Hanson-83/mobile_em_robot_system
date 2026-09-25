# M1 审核整改说明（2026-09-25）

| 项 | 内容 |
|----|------|
| 对象 | M1 契约与骨架 |
| 依据 | `ref/review/review_M1_260925.md` |
| 作者 | Dev_Max |

## 已关闭

| 审核 ID | 级别 | 落点 |
|---------|------|------|
| M1-001 | P1 | `DELETE/PATCH /points/{id}`、`POST /users`；OpenAPI 测试覆盖 |
| M1-002 | P1 | 一轮：prod 弱集合拒绝。二轮（Reviewer_Delta）：Compose 去掉可猜默认改为必填；JWT≥16/口令≥10；`create_app(prod)` 测试；CI git grep 扫描 |
| M1-003 | P1 | `test_rate_limited`：超限 429 + `RATE_LIMITED` |
| M1-004 | P2 | `devices.example.yaml` 去掉内嵌 features，单源 `features.example.yaml` |
| M1-005 | P2 | 测量上报改为 `data.measurement.write` |
| M1-006 | P2 | progress / test.md 按复审结论更正执行者 |
| M1-009 | P2 | PATCH 点位禁止改 id，走 Point 校验 |

## 仍开放（不阻塞 M1）

- M1-007 调度状态机 → **M2**
- M1-008 OpenAPI 快照导出 → M2 末 / M5
