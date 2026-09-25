# 经验教训

## 2026-09-25 上位机首版实现

- Starlette `JSONResponse` 的参数顺序是 `(content, status_code)`。按 `(status_code, content)` 调用会在构造响应时把字典当成状态码，所有业务错误变成 500。
- SQLite 经 SQLAlchemy 读回的 `DateTime` 往往是无时区的。写入与比较统一用 UTC 朴素时间，读出后再规范化，避免和带时区的 `datetime` 比较。
- 粒子 Fake 的瞬时失败计数如果放在 `start_sample` 上，会把本应留给 `read_channels` 的重试次数吃掉，`uncertain` 质量无法出现。启停与读数要分开注入。
- 开发种子账号方便联调，但必须由环境变量关闭。文档和界面都要写明这不是生产口令。
- 前端页面用 Vite 代理 `/api`。浏览器验证要同时看任务是否真的变成 Succeeded，不能只看地图是否渲染。
- 报告若用任务 ID 去匹配报警的 `object_ref`，超限报警实际挂在测量 ID 上，报告会显示「无超限」。关联必须走测量记录。
- 关闭审计开关时，如果先把开关写成 false 再记审计，这条关闭记录会被跳过。必须在开关仍为 true 时先写入。
