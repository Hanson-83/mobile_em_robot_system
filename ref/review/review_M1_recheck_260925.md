# M1 契约与骨架整改复审意见（2026-09-25）

## 1. 审核元信息

| 项 | 内容 |
|----|------|
| 审核对象 | M1 整改差分复审（对照 `ref/review/review_M1_260925.md` 的 P0：M1-C01/C02，P1：M1-C03–C07） |
| 仓库 / 分支 | `/workspace` / `cursor/m1-skeleton-fake-8317` |
| 初审提交 | `16e7dcb feat(m1): 仓库骨架、适配 Fake、Gateway 草图与 Vue 壳` |
| 整改提交 | `dbd465e fix(m1): 按 Reviewer_Code 整改错误体、密钥与 Fake 断言` |
| 审核依据 | 初审意见；`doc/spec/ds.md` §4.2；`spec/security.md`；`spec/testing_quality.md`；`ref/plan.md` §6.2 |
| 抽查范围 | `backend/app/core/errors.py`、`security.py`、`config.py`；`backend/tests/test_error_body.py`、`conftest.py`；`backend/app/adapters/fake/`；`frontend/src/views/LoginView.vue`、`TasksView.vue`；`deploy/docker-compose.yml`；并交叉阅读 `misc.py`、`main.py`、`openapi_v1.sketch.yaml`、`test_gateway.py`、`test_adapters_fake.py`、`test_smoke_task.py`、`test_features_live.py` |
| 审核人 | Reviewer_QA（独立于 Reviewer_Max、Reviewer_Code） |
| 审核日期 | 2026-09-25 |
| 总体结论 | **有条件通过** |

结论说明：P0 两项（统一错误体、默认密钥/内置口令）已从运行路径关闭。P1 中 C04–C07 的功能缺陷已关闭。C03 只完成了路径补齐，权威运行时 schema 仍无统一 Error 模型，静态草图与运行时路径仍漂移，契约测试未锁定草图文件。按初审门禁，M1 尚不能关闭，不宜正式进入 M2。

本复审未改业务代码、未 commit。前端未重跑 `npm run build`，登录页与任务页仅作静态阅读。

## 2. 验证结果

| 检查 | 结果 |
|------|------|
| `cd backend && .venv/bin/pytest -q` | **通过**：16 passed，1 warning（Starlette `TestClient` / anyio 弃用警告） |
| 422 缺字段、404 未知路由 | **通过**：`test_error_body.py` 断言 `code` / `retryable` |
| WebSocket 无 token | **通过**：`AUTH_REQUIRED` 且 `retryable=false` |
| 405（抽查 `PUT /health`，非套件内用例） | 体为 `{code: VALIDATION_ERROR, message, retryable: false}`，HTTP 405 |
| 未处理异常（临时探针路由，非套件内用例） | 体为 `{code: INTERNAL_ERROR, message: 内部错误, retryable: true}`，不回传异常文本 |
| 空密钥 / 短密钥 / `change-me-dev-only` / 生产环境 `MER_ALLOW_DEV_AUTH` | `validate_settings` 均 `RuntimeError` |
| 源码口令与 Compose 默认密钥 | 应用代码与前端无预填口令；Compose 为 `${MER_SECRET:?MER_SECRET is required}`，端口 `127.0.0.1:8000:8000` |

## 3. 逐条复审

| ID | 原级别 | 复审结论 | 验证要点 |
|----|--------|----------|----------|
| M1-C01 | P0 | **已关闭** | `register_exception_handlers` 覆盖 `DomainError`、`RequestValidationError`、`StarletteHTTPException`、未处理 `Exception`。`main.py` 已注册。WS 鉴权错误含 `retryable`。`doc/test.md` TC-MVP-08 仍标「通过（草图）」，与当前测试证据相符，不再把未实现的错误体写成通过。 |
| M1-C02 | P0 | **已关闭** | `security.py` 无内置账号；用户库仅当 `MER_ALLOW_DEV_AUTH` 且 `MER_DEV_USERS_JSON` 存在时加载。`mer_secret` 默认空串，占位值与长度 &lt; 16 拒绝启动；`prod`/`production` 禁止开发用户库。测试口令只在 `tests/conftest.py`。`LoginView.vue` 用户名与密码初始为空。Compose 不提供默认密钥，且只绑定回环地址，`MER_ALLOW_DEV_AUTH=false`。 |
| M1-C03 | P1 | **未关闭（范围收窄）** | 草图已有 `Error` schema，并补上初审点名的 points / limits / users / alarms / reports / approvals 路径。运行时路由覆盖 DS §4.2 最小方法（点位 PATCH/DELETE 在 `/points/{point_id}`，可接受）。未关闭原因见 §4。 |
| M1-C04 | P1 | **已关闭** | `test_adapters_fake.py` 断言 Call 后楼层=2 且门开、Enter 后门关、Exit 后门开，并对 call/enter/exit 分别注入 `DEVICE_OFFLINE`。冒烟除 `elevator_trace` 外核对电梯终态楼层与门。空操作的 Enter/Exit 不再能通过。 |
| M1-C05 | P1 | **已关闭** | `ParticleFake` / `ClimateFake` / `AirflowFake` 支持曲线与 `exceed` 注入；测试覆盖粒子序列推进、温湿度超限、风速曲线与超限。`ref/tasks.md` T-003 保持「部分完成」（厂商 API 仍占位），与 Fake 能力补齐后的真实范围一致。 |
| M1-C06 | P1 | **已关闭** | `TasksView.vue` 挂载时 `GET /api/v1/tasks`，表格渲染列表，创建成功后 `refresh()`。`frontend/README.md` 只称「任务列表」壳，未再把空按钮写成完成功能。无前端组件测试，记 P2，不维持 P1。 |
| M1-C07 | P1 | **已关闭** | `misc.py` 使用 `import app.main_state as state`，请求时读取 `state.features`，不再保存导入时的对象快照。`test_features_live.py` 在置 `e_sign=true` 后同时断言 `/settings/features`、`/settings/limits`、`/ready`。默认 false 由 `test_gateway.py` 的 `/ready` 覆盖。 |

## 4. 问题清单（残留）

| ID | 级别 | 位置 | 问题描述 | 依据 | 建议 |
|----|------|------|----------|------|------|
| M1-C03 | **P1** | `backend/app/api/openapi_v1.sketch.yaml`；`backend/app/main.py` `custom_openapi`；`backend/tests/test_gateway.py` | 草图声明运行时 `/openapi.json` 为权威 schema，但运行时 components **没有** `Error` schema。草图 26 个操作里仅 2 个引用 Error，仍无请求/响应模型。路径参数不一致：草图 `/api/v1/tasks/{id}/cancel`，运行时 `/api/v1/tasks/{task_id}/cancel`。契约测试只断言运行时若干 path/method，不加载草图，不能发现上述漂移。 | DS §4.2 错误体与最小资源表；初审要求选定权威 schema 并做 paths/methods 契约测试。 | 在 `custom_openapi` 写入与 DS 一致的 Error schema，关键响应引用它；草图路径参数与运行时对齐（或测试明确忽略 WS）；契约测试解析 `openapi_v1.sketch.yaml`，比对 DS 最小方法与 Error 引用。 |
| M1-R01 | P2 | `backend/tests/test_error_body.py` | 套件未覆盖 405、429、500 及 401/403 的 `message`+`retryable`。抽查时这几类体已统一。405 的 code 使用 `VALIDATION_ERROR`（DS 错误码表无单独的方法不允许码），语义偏宽。 | 初审 §7 错误矩阵。 | 把 405/429/500 纳入精确断言；405 继续用表内码即可，在草图中写明映射。 |
| M1-R02 | P2 | `doc/technical_manual.md` §2 | 仍写开发账号 `admin/admin`、`operator/operator`。这些口令已不在应用源码中，只存在于测试夹具；手册容易被理解成开箱账号。 | `spec/security.md` 不把口令写入可提交材料。 | 改为「须自行设置 `MER_DEV_USERS_JSON`」，不要列出可直接登录的口令对。 |
| M1-R03 | P2 | `backend/app/core/config.py` `PLACEHOLDER_SECRETS` | 占位值按整串相等拒绝。`changeme-but-long-enough`（长度≥16）可通过校验。空串、`change-me-dev-only`、`secret`、`changeme` 会拒绝。 | 初审要求拒绝占位签名密钥。 | 可保持整串黑名单；若要加强，拒绝包含已知占位词的弱密钥。不恢复为 P0。 |
| M1-R04 | P2 | `backend/tests/test_adapters_fake.py` | 未断言 Call/Enter/Exit 返回的 `CommandHandle`，也未断言失败注入是一次性的（失败后下一次应成功）。实现里 `_fail_next` 会清除。 | 初审建议含命令句柄与一次性恢复。 | 补两条断言即可，当前门状态断言已能抓住空操作退化。 |
| M1-R05 | P2 | `frontend/` | 无组件或 API 测试证明任务列表请求。代码阅读可见 GET 与刷新。 | 初审建议补前端测试后再标 T-006 完成。 | M2/M4 前端测试补上；在此之前 T-006 证据保持为代码审阅。 |
| M1-R06 | P2 | `backend/app/adapters/fake/instruments.py` | 湿度固定 45%，超限只抬高温度；无空曲线边界测试。粒子与风速曲线已可注入。 | plan §6.2 曲线与超限。 | 后续补湿度曲线；不推翻 C05 关闭。 |

初审 P2（M1-C08 `inject` 进入正式 Protocol、M1-C09 锁文件）本次不作为通过条件。Dockerfile 已改为 `pip install -e .`（不再安装 `.[dev]`），锁文件仍未见，C09 维持未关闭 P2。

## 5. 与文档一致性

| 文档/任务 | 复审结论 |
|-----------|----------|
| `doc/test.md` TC-MVP-08 | 与现有错误体测试一致，可维持「通过（草图）」。稳定版仍标 M5。 |
| `ref/tasks.md` T-003 | 「部分完成」合理（Fake 曲线已补，厂商仍占位）。 |
| `ref/tasks.md` T-004 | 「部分完成」合理；在 C03 关闭前不应改为完成。 |
| `ref/tasks.md` T-006 | 任务列表代码已具备。完成证据缺前端测试（M1-R05）。 |
| `doc/technical_manual.md` | 与 C02 整改不一致，见 M1-R02。 |

## 6. 结论与 M2 门禁

- **总体结论：有条件通过。**
- **剩余 P0：无。** M1-C01、M1-C02 关闭。
- **剩余 P1：M1-C03。** M1-C04、M1-C05、M1-C06、M1-C07 关闭。
- **是否可进 M2：否。** 初审要求 P0 与 P1 全部关闭后再进入 M2。C03 仍使静态草图与权威运行时 schema 双轨，M2 若按草图实现取消任务路径会用错参数名，且错误模型未进入 `/openapi.json`。
- **放行条件：** 关闭 M1-C03（运行时 Error schema、草图与运行时路径一致、契约测试覆盖 DS §4.2 最小方法及错误引用）后，可关闭 M1 并进入 M2。M1-R01–R06 不单独挡 M2。
