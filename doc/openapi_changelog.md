# OpenAPI 变更日志

## 1.0.0（2026-09-26，M5 稳定版）

- 状态：`stable`（`info.x-mer-openapi-status`）。
- 版本号：`1.0.0`（运行时 `GET /openapi.json` 与 `GET /api/v1/version`）。
- 分组：`operations` / `data` / `settings` / `integrations`。
- 新增 MES/SCADA/DCS 对接门面：`/api/v1/integrations/mes/*`。
- 支持服务账号长 Token：环境变量 `MER_API_TOKENS_JSON`。
- 破坏性变更策略：保留 `/api/v1` 兼容；破坏性变更走 `/api/v2`。
- **不交付**：桌面客户端、移动客户端（分期立项）。

## 0.1.0（M1 草图）

- 文件：`openapi_v1.sketch.yaml`（历史保留，不再作为契约权威）。
- 覆盖 Gateway 最小资源表草图与 Fake 冒烟路径。
