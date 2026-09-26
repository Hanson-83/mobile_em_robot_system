# M5 审核整改说明（2026-09-26）

依据 `ref/review/review_M5_260926.md`（Reviewer_API，有条件通过）。

| 问题 | 处理 |
|------|------|
| M5-001 静态/runtime 路径漂移 | 按 runtime 回写 `openapi_v1.stable.yaml`（含 `/admin/backup|restore`、`{approval_id}`、`trends` 等）；`/api/v1/ws` 保留为 allowlist |
| M5-002 `client_request_id` 非幂等 | kv 映射 `mes:client_request_id:*` → 重复 POST 返回原任务 |
| M5-003 契约对称测试不足 | `test_stable_catalog_paths_present` 全量 path/method 对称 + WS allowlist |
| M5-004 realtime 字段差 | 抽取 `build_realtime_snapshot()`，Web/MES/WS 共用 |
| M5-005 WS 不认服务账号 | `ws_gateway` 改 `resolve_bearer` |
| M5-006 MES schema 薄弱 | stable 增加 `MesTaskCreate` 与幂等说明 |
| M5-007 Token 比较 | `hmac.compare_digest`；非法 JSON → `DomainError` |

验证：`pytest` 41 passed。建议复审后冻结 OpenAPI 1.0.0。
