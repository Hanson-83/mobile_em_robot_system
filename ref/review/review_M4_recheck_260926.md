# M4 P1 复核意见（2026-09-26）

## 1. 审核元信息

| 项 | 内容 |
|----|------|
| 审核对象 | 原审核 `ref/review/review_M4_260926.md` 的 P1：M4-001～M4-005（实时通道、地图示意图、用户组说明、批准中心引导） |
| 仓库 / 分支 | `/workspace` / `cursor/m4-vue-mvp-8317` |
| 对照提交 | 原审核 `e0a24c7`；整改 `0198603`（`fix(m4): 地图示意、实时通道与批准引导`）；说明 `0bfb886`；复核时 HEAD `0bfb886` |
| 阅读范围 | `frontend/src/views/MapView.vue`、`AlarmsView.vue`、`PointsView.vue`、`UsersView.vue`；对照 `TrendsView.vue`、`frontend/vite.config.ts`、`frontend/src/api/client.ts`；`backend/app/api/routes/misc.py` 的 `/api/v1/ws` 与 `_live_snapshot`；`backend/tests/test_error_body.py` |
| 审核人 | **Reviewer_Walk** |
| 审核日期 | 2026-09-26 |
| 总体结论 | **通过** |

结论说明：四项 P1 均按原审核给出的最低闭环方式关闭。Gateway `GET` 式 WebSocket `/api/v1/ws` 在 hello 之后约每 2 秒推送 `type=snapshot`（机器人状态含位姿、报警列表）；地图页与报警页用当前页主机的 `/api/v1/ws?token=` 订阅，开发代理已开 `ws: true`。地图页用 SVG 圆点表示位姿。用户页写明没有独立用户组、账号来自环境变量、本页只读，与 `GET /api/v1/users` 及仍开放的 Q-05 一致。限值遇到 `APPROVAL_REQUIRED` 时清空错误区，并在有 `approval_id` 时给出到 `/approvals` 的链接。本次只读复核，未改业务代码、未 commit。`cd /workspace/backend && .venv/bin/pytest -q`：**37 passed**，1 warning。`cd /workspace/frontend && npm run build`：**通过**。未再跑浏览器。

## 2. 验证结果

| 检查 | 结果 |
|------|------|
| 后端测试：`cd /workspace/backend && .venv/bin/pytest -q` | **通过**：37 passed，1 warning（Starlette/anyio 弃用） |
| WS 用例 | `tests/test_error_body.py::test_ws_snapshot_follows_hello`：hello 之后收到 `type=snapshot`，含 `alarms`、`robots`；无 token 仍为 `AUTH_REQUIRED` 且 `retryable=false` |
| 快照抽查（TestClient，开发用户库） | hello 主题为 `pose/task/alarm/measurement`；快照键只有 `type/alarms/robots`。默认 `robot-01` 的 `status.pose` 为 `{x:0,y:0,theta:0}`，`mode` 为字符串 `idle` |
| 前端构建：`cd /workspace/frontend && npm run build` | **通过**（`vue-tsc -b && vite build`） |
| 浏览器 | **未复测**。整改说明称地图示意图与「实时通道已连接」已在浏览器看到；本次以源码与接口为准 |

## 3. P1 逐项

| ID | 原问题 | 复核 | 证据 |
|----|--------|------|------|
| M4-001 | 前端未建立 WebSocket；趋势、报警、批准状态与 DS 实时通道不一致 | **关闭** | 原建议的最低标准是「经 Gateway 至少一条 MVP 推送」。`misc.py` `ws_gateway`：鉴权后发 hello，客户端 2 秒无文本则 `_live_snapshot()`。快照含机器人（位姿在 `status.pose`）和全部报警。地图、报警两页已连接。趋势曲线与批准结果推送不在本条关闭范围内，见 §4。 |
| M4-005 | 报警无推送，只能整页刷新 | **关闭** | `AlarmsView.vue` 在 `GET /api/v1/alarms` 之后订阅同一 WS；`type===snapshot` 且带 `alarms` 时替换列表，并显示「报警列表由实时通道刷新」。确认/关闭仍走 HTTP，成功后再拉一次列表。 |
| M4-002 | 地图只有表格，无可视化 | **关闭** | `MapView.vue` 增加 `viewBox="0 0 240 140"` 的 SVG：圆点 `cx=20+x*12`、`cy=110-y*12`，旁注机器人 ID。默认位姿 (0,0) 落在画布内。这是原建议中的最小 2D 示意图，不是地图底图或轨迹。 |
| M4-003 | 用户页无组、无管理 | **关闭（范围说明）** | `UsersView.vue` 写明：账号来自环境变量、本页只读、当前没有独立用户组、角色即权限边界、生产目录仍待确认。`GET /api/v1/users` 只返回 `username` 与 `roles`；`POST /api/v1/users` 为 `NOT_IMPLEMENTED`。后端没有用户组资源可接。Q-05（生产用户目录）仍开放。 |
| M4-004 | 批准被拦时无批准中心入口，且错误与提示同时出现 | **关闭** | `PointsView.vue` `saveLimit`：`ApiError.code===APPROVAL_REQUIRED` 时写入说明「限值尚未生效，请到批准中心由其他用户签署」，`error` 置空。模板在 `approvalId` 非空时渲染 `RouterLink` 到 `/approvals`。后端 `request_limit_change` 在签名开启时 details 带 `approval_id`。非批准类失败仍只进错误区。 |

## 4. 观察（不升为未关闭 P1）

| 项 | 说明 |
|----|------|
| 趋势仍是历史查询 | `TrendsView.vue` 仍写「实时推送仍为 WebSocket 占位」，只在点击查询时 `GET /trends`。原 P1 建议允许「至少一条」推送；整改也只承诺地图和报警。DS §4.3 所列任务进度、测量推送未进快照。 |
| hello 主题宽于快照 | hello 宣布 `pose/task/alarm/measurement`，快照没有 `task`、`measurement` 字段。位姿嵌在 `robots[].status.pose`，没有单独的 pose 事件。函数注释仍写「实时通道占位」。 |
| 断线 | 两端都没有按 DS §4.3 做心跳重连和按主题过滤。地图页仅 `onerror` 时改文案；报警页没有 `onerror`/`onclose`。快照里 `amr.get_status()` 在机器人离线时抛 `DEVICE_OFFLINE`，该异常不在 WS 循环的捕获范围内，连接会因此结束。默认 `start_all` 之后 Fake 在线，正常快照已抽查通过。 |
| 地图示意图边界 | 点位仍是列表，未画进 SVG。页眉仍写「地图格式暂为 GeoJSON 点位占位」。x 大于约 18 或 y 大于约 9 时圆点超出 viewBox。无朝向、无轨迹。URS-SCH-005 的载入地图与轨迹不在本次关闭标准内。 |
| 批准链接残留 | `approvalId` 在再次保存时不重置。上一次被批准流拦住之后，若下一次直接生效，成功句「限值已生效」旁仍会留下「打开批准中心」。链接不带具体 `approval_id`。首次被拦住时错误区不再同时变红，原 P1 现象已消除。 |
| 批准结果无 WS | DS §14.3 序列图在批准完成后有 `WS approval Approved`。页面用链接代替，批准中心仍靠打开页面后的 HTTP 列表。 |
| 令牌位置 | WS 令牌在查询串。与 HTTP Bearer 不同，代理访问日志可能记下令牌。不在原 P1 条目内。 |

## 5. 是否可作为 Web MVP 冻结基线

| 项 | 结论 |
|----|------|
| M4-001～M4-005 | **已关闭，不再阻塞把 M4 页面冻为 Web MVP 基线** |
| M4-006～M4-010（P2） | 仍开放。原审核未把它们当作冻结门槛 |
| 真机 | **不在本次范围**。基线对应 Fake AMR 与 Gateway |
| 是否可作为 Web MVP 冻结基线 | **可以**。冻结的是当前十页在 Fake 上的页面行为：登录与 Gateway 路径仍按原审核成立，实时通道至少覆盖地图位姿与报警列表，地图有位姿示意图，用户组缺口已在页面写明，限值批准有进入批准中心的引导。 |
| 不应一并写成已完成的部分 | 趋势实时、任务/测量 WS、断线重连、地图底图与轨迹、用户组 CRUD、批准结果 WS。这些不推翻本次 P1 关闭，也不把本基线写成 URS-CLI-001 / DS §4.3 的字面终验。 |

---

**返回摘要（给协调方）**

- **结论**：通过
- **P1**：M4-001、M4-002、M4-003、M4-004、M4-005 均关闭
- **M4 页面是否还可作为 Web MVP 冻结基线（真机不在范围）**：**可以**
