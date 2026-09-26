# M5 Gateway / OpenAPI 整改复审意见（2026-09-26）

## 1. 审核元信息

| 项 | 内容 |
|----|------|
| 审核对象 | 初审 `ref/review/review_M5_260926.md` 的 P1（M5-001～003）与 P2（M5-004～007）整改闭环 |
| 整改说明 | `ref/review/remediation_M5_260926.md` |
| 仓库 / 分支 | `/workspace` / `cursor/m5-gateway-openapi-8317` |
| 初审提交 | `8c3ba5a` — `feat(m5): OpenAPI 1.0.0 稳定版与 MES 对接门面` |
| 复审提交 | `d28720a` — `fix(m5): 对齐稳定契约、MES 幂等与审核 P1/P2`（`git log -1` 确认） |
| 审核依据 | 初审问题清单；`openapi_v1.stable.yaml`；`integrations.py`；`test_mes_integration.py`；相关 runtime 与 `core/integrations.py` / `misc.py` / `services/realtime.py` |
| 审核人 | **Reviewer_API_Recheck** |
| 审核日期 | 2026-09-26 |
| 总体结论 | **通过** |

结论说明：初审三项 **P1** 与四项 **P2** 均已按整改说明落地；`pytest` **41 passed**。静态 stable 与 runtime HTTP paths/methods 对称（`/api/v1/ws` 显式 allowlist）；MES `client_request_id` 幂等有实现与测试；realtime 共用快照；WS 走 `resolve_bearer`；Token 比较与非法 JSON 处理已加固。工作区另有未提交的 `misc.py` 无用 import 删除（1 行），不影响结论。**建议冻结 OpenAPI 1.0.0 stable。**

## 2. 验证结果

| 检查 | 结果 |
|------|------|
| `cd /workspace/backend && . .venv/bin/activate && python -m pytest -q` | **通过**：41 passed（1 warning：Starlette/anyio `BlockingPortal` 弃用） |
| OpenAPI 版本 / 状态 | **符合**：stable YAML 与运行时均为 `1.0.0` / `x-mer-openapi-status=stable`（测试 `test_api_version_stable`） |
| stable ↔ runtime 对称 | **符合**：`test_stable_catalog_paths_present` 全量 path + method；`stable_only_allowlist={/api/v1/ws}`；含 `/admin/backup`、`{approval_id}/decide` |
| MES 幂等 | **符合**：同 `client_request_id` 两次 POST 返回同一 `task.id`（`test_mes_task_lifecycle_and_realtime`） |
| Web / MES realtime 字段 | **符合**：共用 `build_realtime_snapshot()`；测试断言两边 key 集合相等 |
| 服务账号 Token | **仍可用**：`MER_API_TOKENS_JSON` + Bearer（既有 `test_api_token_auth`） |
| 桌面 / 移动分期 | **维持**：`deferred` 含 desktop/mobile；本版无客户端交付 |

## 3. P1 逐项闭环

| ID | 原问题 | 复审 | 证据 |
|----|--------|------|------|
| M5-001 | stable 与 runtime 路径漂移；`/backup` 404 | **关闭** | `openapi_v1.stable.yaml` 已改为 `/api/v1/admin/backup|restore`、`/approvals/{approval_id}/decide`、`/trends`、`/robots/{robot_id}/navigate` 等；旧 `/backup`/`/restore`/`{id}/decide` 已移除；`/api/v1/ws` 保留并在 `info.x-mer-websocket` 声明「通常不进 runtime paths」 |
| M5-002 | `client_request_id` 仅回写非幂等 | **关闭** | `integrations.create_task`：`mes:client_request_id:*` blob 映射；命中则返回原任务；catalog `idempotency` 文案与 YAML `MesTaskCreate.client_request_id` 说明一致；测试重复 POST 同 id |
| M5-003 | 契约测试未覆盖漂移 | **关闭** | `test_stable_catalog_paths_present`：stable−allowlist == runtime paths，且逐 path 比对 HTTP method；断言 backup/approvals 参数名在 runtime 中 |

## 4. P2 逐项闭环

| ID | 原问题 | 复审 | 证据 |
|----|--------|------|------|
| M5-004 | Web/MES realtime 字段不一致 | **关闭** | `app/services/realtime.py::build_realtime_snapshot`；`misc` / `integrations` / WS `_live_snapshot` 共用；测试 key 集合相等 |
| M5-005 | WS 不认服务账号 Token | **关闭** | `misc.ws_gateway` 调用 `resolve_bearer`（非仅 `parse_token`）；stable `x-mer-websocket.auth` 已更新 |
| M5-006 | MES request/response schema 薄弱 | **关闭（最低闭环）** | 增加 `components.schemas.MesTaskCreate`，`POST .../mes/tasks` 挂 `requestBody`；幂等字段有 description。其余 MES 响应仍偏目录式，不阻塞冻结 |
| M5-007 | Token 非恒定时间比较；非法 JSON 可能炸鉴权路径 | **关闭** | `hmac.compare_digest` 遍历；`JSONDecodeError` → `DomainError`。**残留（不升 P1）**：非法 JSON 未在启动期 `validate_settings` fail-fast，仍在鉴权时抛 DomainError——可作后续 P3 硬化 |

## 5. 观察（不阻塞）

| 项 | 说明 |
|----|------|
| stable 仍为路径目录为主 | 非 MES 路径多数无详细 response schema；权威运行时仍以 `GET /openapi.json` 为准（YAML description 已声明） |
| WS 不在 runtime OpenAPI paths | 刻意 allowlist；对接方需读 `x-mer-websocket` |
| 幂等存储 | 依赖 store blob；任务被删后同 `client_request_id` 会重新创建（映射失效）——可接受，建议日后文档一句说明 |
| 工作区脏文件 | `misc.py` 删除未用 `asdict` import（未提交）；`remediation_M5_260926.md` 在复审时为工作区可见说明。复审以 `d28720a` 树为准 |

## 6. 是否建议冻结 OpenAPI 1.0.0

| 项 | 建议 |
|----|------|
| 总体 | **通过** |
| **剩余 P0** | **0** |
| **剩余 P1** | **0**（初审 M5-001～003 均关闭） |
| **剩余 P2** | **0**（初审 M5-004～007 均关闭；M5-007 仅可选启动期校验残留，不记为开放 P2） |
| **正式冻结 OpenAPI 1.0.0 stable** | **建议冻结** |
| MES 门面 | 可正式对接试用（含幂等重试） |
| 桌面/移动 | **维持分期**，不阻塞本里程碑 |

## 7. 与初审结论对比

| 项 | 初审 | 复审 |
|----|------|------|
| 结论 | 有条件通过 | **通过** |
| 冻结 1.0.0 | 暂不建议（待 P1） | **建议冻结** |
| P1 开放数 | 3 | **0** |
| P2 开放数 | 4 | **0** |

---

**返回摘要（给协调方）**

- **结论**：通过  
- **P0**：无（0）  
- **P1**：无（0）；M5-001、M5-002、M5-003 均关闭  
- **P2**：M5-004～007 均关闭  
- **是否建议冻结 OpenAPI 1.0.0**：**是**  
- **审核文件**：`ref/review/review_M5_recheck_260926.md`  
