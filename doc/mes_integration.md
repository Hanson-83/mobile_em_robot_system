# MES / SCADA / DCS 对接说明（M5）

## 范围（已确认）

首批仅开放：

1. 任务下发
2. 任务启停
3. 任务状态查询
4. 实时数据读取

桌面/移动客户端**不在本版本**；破坏性 API 变更走 `/api/v2`。

## 鉴权

| 方式 | 说明 |
|------|------|
| 会话 Token | `POST /api/v1/auth/login` → `Authorization: Bearer <token>` |
| 服务账号 Token | 环境变量 `MER_API_TOKENS_JSON`，值为 token→元数据映射 |

示例：

```bash
export MER_API_TOKENS_JSON='{"mes-token-demo":{"client_id":"mes-line-a","roles":["api_client"],"perms":["operations.task.read","operations.task.write","data.measurement.read","data.alarm.read","data.robot.read","data.map.read"]}}'
```

## 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/integrations/mes/catalog` | 能力目录 |
| POST | `/api/v1/integrations/mes/tasks` | 下发（`auto_start` 默认 true；`client_request_id` **幂等**） |
| GET | `/api/v1/integrations/mes/tasks` | 列表 |
| GET | `/api/v1/integrations/mes/tasks/{id}` | 状态 |
| POST | `/api/v1/integrations/mes/tasks/{id}/start` | 启动 |
| POST | `/api/v1/integrations/mes/tasks/{id}/stop` | 停止 |
| GET | `/api/v1/integrations/mes/realtime` | 实时快照（与 `/api/v1/realtime` 同结构） |

与 Web 主路径 `/api/v1/tasks*`、`/api/v1/realtime` 共用同一调度与存储，避免双实现。

## 契约

- 静态目录：`backend/app/api/openapi_v1.stable.yaml`
- 运行时权威：`GET /openapi.json`
- 版本摘要：`GET /api/v1/version`
- 变更记录：`doc/openapi_changelog.md`

## 错误体

统一 `{code, message, retryable, details?}`，与 Gateway 一致。
