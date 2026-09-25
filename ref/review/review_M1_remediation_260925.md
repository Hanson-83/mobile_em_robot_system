# M1 P1 整改差分复审意见（2026-09-25）

## 1. 审核元信息

| 项 | 内容 |
|----|------|
| 审核对象 | 分支 `cursor/m1-contract-skeleton-748b` 上、相对提交 `55f07ea` 的 **未提交工作区** — M1 P1 整改（`ref/review/remediation_note_M1_260925.md`） |
| 审核性质 | 差分复审。审核人独立于实现者 Dev_Max 与初审 Reviewer_QA |
| 初审结论 | `ref/review/review_M1_260925.md`：**有条件通过**（P0=0，P1=M1-001/002/003） |
| 审核依据 | 初审意见与整改说明；`doc/spec/ds.md` §4.2；`ref/project_scheme.md` §4.3.1、§8.1；`ref/plan.md` §6.4 DoD；`spec/security.md` |
| 代码范围 | `backend/app/api/routes.py`、`backend/app/core/config.py`、`backend/app/core/security.py`、`backend/app/main.py`、`backend/app/services/auth_users.py`、`backend/app/services/stores.py`、`backend/tests/test_gateway.py`、`config/devices.example.yaml`、`deploy/.env.example`、`deploy/docker-compose.yml`；并核对同批工作区中的 `deps.py`、`doc/test.md`、`ref/progress.md`、`.github/workflows/ci.yml` |
| 审核人 | Reviewer_Delta |
| 审核日期 | 2026-09-25 |
| 验证执行 | 一轮：pytest **22 passed**，ruff 通过。二轮（§10）：pytest **24 passed**，ruff 通过；另探针 `create_app(env=prod)`、PATCH 与 CI `git grep` 的工作目录 |
| 总体结论 | **通过**（二轮覆写一轮的「有条件通过」）。M1-001、M1-002、M1-003 均关闭。**建议进入 M2。** 第一轮正文见 §2–§7；现行判定以 §8 与 §10 为准。 |

---

## 2. 总体评价

整改说明声称 M1-001/002/003 均已关闭。差分核对后，**路由补齐与限流测试达到初审闭合标准**；**生产弱密钥门禁只覆盖显式 `MER_ENV=prod`，仓库给出的 Compose 默认启动路径仍使用可猜 JWT 与口令，门禁不会执行**。因此三项 P1 不能一并关闭。

P2 方面：特性单源（M1-004）与测量上报权限（M1-005）代码上成立。进度与测试记录（M1-006）在差分复审完成前写了「P1 已整改、下一步 M2」，并把「整改后 22 passed」记在 Reviewer_QA 名下；本复审独立复跑确认 22 passed，执行者归属不成立。调度状态机（M1-007）与 OpenAPI 快照（M1-008）仍按初审留到 M2/M5。

本次新增路由中，`PATCH /points/{point_id}` 用未校验的裸字典更新模型，点位 `id` 可与存储键分裂，记为新的 P2（M1-009），不据此重新打开 M1-001。

---

## 3. 符合项（本轮整改中成立的部分）

- **点位 DELETE 与用户 POST 已进入 Gateway 与 OpenAPI**。`/openapi.json`：`/api/v1/points` 为 `get`/`post`；`/api/v1/points/{point_id}` 为 `patch`/`delete`；`/api/v1/users` 为 `get`/`post`。权限码为 `settings.point.write` / `settings.user.write`。
- **DELETE / 用户创建行为可用**。`test_point_delete_and_user_create` 断言 201 与 204。探针：不存在点位 `404 NOT_FOUND`；任务 `skills[].params.point_id` 引用时 `422 VALIDATION_ERROR`；viewer 删除点位与创建用户均为 `403 FORBIDDEN`；重复用户名 `422`；未知角色 `422`；新建用户可登录，响应不含口令哈希。
- **限流集成测试打在真实依赖链上**。`get_principal` 以 `principal.sub` 调用 `TokenRateLimiter.check`；`test_rate_limited` 把 `per_min` 调到 2 后，第三次 `GET /tasks` 为 `429`、`code=RATE_LIMITED`、`retryable=true`。`client` fixture 为函数级，该改写不泄漏到其他用例。
- **`MER_ENV=prod` 且密钥命中弱集合时，进程拒绝启动**。`create_app` 调用 `assert_runtime_secrets`。探针：默认 `Settings` 且 `env=prod` 抛出 `RuntimeError`（文案指向 `MER_JWT_SECRET`）。
- **viewer 口令走配置**。`bootstrap_directory` 接收 `viewer_password`；`MER_BOOTSTRAP_VIEWER_PASSWORD` 出现在 `Settings`、`.env.example`、`docker-compose.yml`。源码里不再写死字面量 `"viewer"` 作为唯一口令来源（开发默认值仍为 `"viewer"`，见 M1-002）。
- **测量上报权限已改为 `data.measurement.write`**。admin/operator/api_client 拥有该码，viewer 没有。探针：viewer `POST /measurements` 返回 403，消息为缺少 `data.measurement.write`。既有幂等用例仍以 admin 通过。
- **示例设备文件不再内嵌 `features`**。`config/devices.example.yaml` 仅保留指向 `features.example.yaml` 的注释；运行时仍由 `MER_FEATURES_PATH` 加载特性文件。
- **测试数量与 lint**。pytest 22 passed（初审记录为 19，增加限流、点位/用户、生产弱密钥三则）；ruff 通过。

---

## 4. 问题清单

> 以下为**第一轮**判定。M1-002、M1-009 的现行状态以 §10 为准。

### 4.1 初审项闭合判定

| ID | 初审级别 | 整改说明 | 复审判定 | 证据摘要 |
|----|----------|----------|----------|----------|
| M1-001 | P1 | 已关闭 | **关闭** | DELETE/PATCH `/points/{point_id}`、POST `/users` 已注册；OpenAPI 方法见 §3；`test_point_delete_and_user_create` 与探针覆盖删除、创建、403/404/422。PATCH 质量残留见 M1-009 |
| M1-002 | P1 | 已关闭 | **未关闭** | 见下方问题表。门禁函数存在，默认部署路径不经过该门禁 |
| M1-003 | P1 | 已关闭 | **关闭** | `test_rate_limited`：同一 admin `sub` 第 3 次请求 429 + `RATE_LIMITED` + `retryable=true`；与 `deps.get_principal` → `rate_limiter.check(principal.sub)` 一致 |
| M1-004 | P2 | 已关闭 | **关闭** | `devices.example.yaml` 已去掉内嵌 `features`。`DevicesFile.features` 与 `load_features` 的内嵌兼容分支仍在，示例不再双源 |
| M1-005 | P2 | 已关闭 | **关闭** | `ingest_measurement` 要求 `data.measurement.write`；`ROLE_PERMS` 已同步。套件内无单独权限断言，探针已确认 viewer 403 |
| M1-006 | P2 | 已关闭 | **部分关闭** | `progress.md` / `test.md` 有更新，但在本复审之前将 P1 写成已完成并指向 M2；`TC-M1-REVIEW-RERUN` 执行者写成 Reviewer_QA。本复审独立结果为 22 passed，该行归属应改为实际执行人 |
| M1-007 | P2 | 仍开放（M2） | **维持开放** | 工作区仍无调度状态机。与整改说明一致，不阻塞本次 P1 判定 |
| M1-008 | P2 | 仍开放（M2 末/M5） | **维持开放** | 仍只有运行时 `/openapi.json`。与整改说明一致 |

### 4.2 仍开放与本轮新增

| ID | 严重级别(P0/P1/P2) | 位置/章节 | 问题描述 | 依据（URS/requirement/规范条款） | 整改建议 |
|----|-------------------|-----------|----------|----------------------------------|----------|
| M1-002 | P1 | `backend/app/core/config.py` `Settings`/`assert_runtime_secrets`；`deploy/docker-compose.yml`；`deploy/.env.example`；`.github/workflows/ci.yml` | **生产误用默认密钥的门禁未罩住仓库默认启动方式。** `assert_runtime_secrets` 在 `env != "prod"` 时直接返回。`Settings.env` 默认 `dev`；Compose 为 `MER_ENV: ${MER_ENV:-dev}`，同时仍展开 `MER_JWT_SECRET:-dev-only-change-me`、`MER_BOOTSTRAP_*:-admin/operator/viewer`。按该文件启动保持可猜口令与 JWT。弱集合仅为精确匹配 `{"" , change-me, dev-only-change-me, admin, operator, viewer}`：探针中 `MER_ENV=prod` 且 JWT/三口令均为单字符时 `create_app` **可以启动**。`features.security.password_min_len=8` 未用于 `UserDirectory.create`（口令 `short` 可创建并登录）。CI 仍只有 ruff 与 pytest，无 scheme §8.1 要求的密钥扫描。`test_prod_rejects_weak_secrets` 只调用辅助函数；其「弱」用例沿用 fixture 的 `jwt_secret=test-secret`（不在弱集合），拒绝来自 bootstrap 口令，不能单独证明默认 JWT 被拒。源码默认值 `dev-only-change-me` / `admin` / `operator` / `viewer` 仍在。 | 初审 M1-002；`spec/security.md`（机密不进源码，安全默认偏保守）；`ref/plan.md` §6.4 DoD；`ref/project_scheme.md` §8.1 | 默认部署必须经过门禁：Compose 去掉可猜默认，改为必填 `.env`（或 `MER_ENV` 默认 `prod` 且缺密钥即拒绝启动）。弱密钥增加最小长度（JWT 与口令至少对齐 `password_min_len`）。测试改为 `create_app(Settings(env="prod"))` 期望 `RuntimeError`，并单独覆盖「口令已加强、JWT 仍为默认值」。CI 增加对默认口令字面量的扫描或等价检查。 |
| M1-006 | P2 | `ref/progress.md`；`doc/test.md` `TC-M1-REVIEW-RERUN` | **行政记录超前于本复审。** progress 写「P1 已整改」且后续行动第 1 步仍是「差分复审关闭 M1-001..003」，同时把阶段指向 M2。`test.md` 将整改后 22 passed 的执行者记为 Reviewer_QA；初审记录的 Reviewer_QA 复跑是 19 passed。本文件发布前，该 22 passed 行应由 Dev_Max 署名。 | `AGENTS.md` progress/test.md；初审 M1-006 | 本复审结论写入后，progress 保持 M1「有条件通过 / M1-002 开放」。`TC-M1-REVIEW-RERUN` 改执行者；另增一行 Reviewer_Delta、22 passed、结论指向本文件。M1-002 关闭后再把 M1 标完成。 |
| M1-009 | P2 | `routes.py` `patch_point`；`stores.py` `update_point` | **点位 PATCH 未校验请求体。** `model_copy(update=patch)` 不走 `Point` 校验。探针：`PATCH /points/P1` 提交 `{"id":"P-EVIL"}` 返回 200，列表中的 `id` 变为 `P-EVIL`，存储键仍为 `P1`（随后 `DELETE /points/P1` 仍命中该对象）。`pose` 以裸 dict 写入，响应丢失未提交的 `theta`/`floor`，并出现 Pydantic `PydanticSerializationUnexpectedValue`。`test_gateway.py` 未调用 PATCH。 | `doc/spec/ds.md` §4.2 点位 PATCH 语义；初审 M1-001 对 PATCH 语义的要求（路由已有，语义未稳） | 请求体改为 `Point` 的部分模型并 `model_validate`；禁止修改 `id`，或修改时同步字典键。补 PATCH 成功、非法 pose、改 id 被拒三条测试。 |
| M1-007 | P2 | 编排 / plan §8(4) | 调度状态机与电梯技能编排仍未开始。 | `ref/plan.md` §1.2 M2 | 维持到 M2，且排在 M1-002 收口之后。 |
| M1-008 | P2 | OpenAPI 工件 | 无版本化 `openapi.yaml`。另：OpenAPI 3 路径表中无 `/api/v1/ws`（探针为缺路径）；WebSocket 处理函数仍在 `routes.py`。测试把初审断言从 `/api/v1/ws` 改为 `/api/v1/ws/info`。`GET /ws/info` 能说明通道，不能代替 WS 路径出现在契约快照中。 | plan M5；`interface_contracts.md`；DS §4.2 WS 行 | M2 末或 M5 导出快照时同时记录 WS 路径；在此之前保留对 `@ops.websocket("/ws")` 的存在性测试，避免只断言 `/ws/info`。 |

---

## 5. 重点核对项（M1-001 / M1-002 / M1-003）

| 核对项 | 结果 | 证据摘要 |
|--------|------|----------|
| M1-001 点位 DELETE | **通过** | 路由 + OpenAPI `delete`；测试 204；404 / 引用 422 / viewer 403 |
| M1-001 点位 PATCH | **路由存在，语义未稳** | OpenAPI 有 `patch`；行为缺陷记 M1-009，不维持 M1-001 |
| M1-001 用户 POST | **通过** | OpenAPI `post`；201；列表可见；可登录；viewer 403；重复与坏角色 422 |
| M1-001 OpenAPI 测试 | **路径级通过** | `test_openapi_groups` 断言路径键；方法集合由本复审读取 `/openapi.json` 确认 |
| M1-002 生产拒绝默认 JWT/口令 | **未通过** | 仅 `MER_ENV=prod` 且命中精确弱集合时拒绝。Compose 与 `Settings` 默认 `dev` + 可猜默认值。单字符密钥在 prod 下可启动。无 CI 扫描 |
| M1-002 viewer 口令环境变量 | **通过（开发默认仍在）** | `MER_BOOTSTRAP_VIEWER_PASSWORD` 接入 bootstrap；默认值仍为 `viewer` |
| M1-003 同一 sub 超限 429 | **通过** | `test_rate_limited`；错误体 `RATE_LIMITED` 且 `retryable=true`；限流键为 `principal.sub` |

---

## 6. 与初审结论的关系

| 初审判断 | 复审后 |
|----------|--------|
| M1 四项完成标志（适配草案、Gateway 草图、目录骨架、Fake 冒烟）主体达标 | **维持**。本轮差分未发现这些标志回退。同批工作区另有换行、`StrEnum`、`ruff` `line-length` 100→110 与 `ignore = ["B008"]`，未改变上述标志 |
| P1 整改后再宣告 M1 门禁并启动 M2 | **M1-002 仍开放，门禁条件未满足** |
| M1-007 / M1-008 不阻塞当时的「有条件通过」 | **维持**。它们也不替代 M1-002 |

---

## 7. 后续验证关注点

- 收口 M1-002 时复跑：`create_app` 在 prod+默认密钥下失败；prod+非默认但过短密钥失败；dev Compose 不再静默注入 `admin` / `dev-only-change-me`。
- 收口 M1-009 时复跑 PATCH：改名成功、非法 `pose` 为 422、请求体中的 `id` 不能造成路径键与模型 `id` 不一致。
- 限流回归保持 `test_rate_limited` 在默认 pytest 内。
- 前端 typecheck 本轮未跑；下次改 `frontend/` 时按初审方式复跑。
- M2 技术项（状态机、TC-MVP-11/12、OpenAPI 快照）仍有效，启动顺序晚于 M1-002。

---

## 8. 结论

**通过。**（本轮覆写第一轮「有条件通过」。依据与残留见 §10。）

- **M1-001：关闭。**
- **M1-002：关闭。**
- **M1-003：关闭。**

**建议进入 M2。** M1 门禁可以宣告完成。M1-007（调度状态机与电梯技能编排）作为 M2 首项。M1-008、M1-010、M1-011 不阻挡进入 M2。

---

## 9. 审核签字

- 审核人：**Reviewer_Delta**
- 日期：**2026-09-25**
- 角色：独立复审（非 Dev_Max，非 Reviewer_QA）
- 第一轮签字维持；二轮结论见 §10

---

## 10. 二轮复审（2026-09-25）

### 10.1 范围

针对第一轮未关闭的 **M1-002**，以及第一轮新增的 **M1-009**。仍只审工作区相对 `55f07ea` 的未提交整改，不改业务代码。

核对文件：`deploy/docker-compose.yml`、`backend/app/core/config.py`、`backend/app/main.py`、`backend/app/services/auth_users.py`、`backend/app/services/stores.py`、`backend/app/api/routes.py`、`backend/tests/test_gateway.py`、`.github/workflows/ci.yml`。

验证：`python3 -m pytest` **24 passed**；`ruff check app tests` 通过。探针调用 `create_app` 与 `PATCH /points/P1`。在 `backend/` 目录复现 CI 的 `git grep` 路径。

### 10.2 M1-002 判定：**关闭**

| 第一轮缺口 | 二轮证据 | 结果 |
|------------|----------|------|
| Compose 展开 `dev-only-change-me` / `admin` / `operator` / `viewer` | `deploy/docker-compose.yml` 四项均为 `${VAR:?set VAR}`，文件中无 `dev-only-change-me`。`test_compose_requires_secrets` 断言该字符串不出现，并断言 JWT 必填语法 | **已收口** |
| prod 下单字符密钥可启动 | `assert_runtime_secrets`：JWT 在弱集合内或长度不足 16 则拒绝；三口令在弱集合内或长度不足 10 则拒绝。探针 `create_app`：prod+源码默认、prod+`short` JWT、prod+默认 JWT 且强口令、JWT 15 字符、口令 9 字符均为 `RuntimeError`；JWT 16 字符且口令 10 字符可以启动 | **已收口** |
| 测试未走 `create_app`，也未单独打默认 JWT | `test_prod_rejects_weak_secrets` 对 prod+fixture 默认密钥调用 `create_app` 并期望 `RuntimeError`；默认 JWT、短 JWT 由 `assert_runtime_secrets` 覆盖。探针确认这两条同样使 `create_app` 失败 | **已收口** |
| 用户口令未用 `password_min_len` | `create_user` 传入 `features.security.password_min_len`（示例为 8）。探针：口令 `short` 为 422 `密码长度不足 8` | **已收口** |
| CI 无密钥扫描 | 工作流增加 Secret scan 步骤；等价检查由 pytest 的 `test_compose_requires_secrets` 在同一 backend job 中执行。步骤本身的 `git grep` 路径见 M1-011，不维持本 P1 | **P1 关闭，扫描步骤残留见 M1-011** |

开发路径仍保留：`Settings` 在 `env=dev` 时默认 `dev-only-change-me` / `admin` / `operator` / `viewer`；`MER_ENV` 在 Compose 中默认 `dev`；`.env.example` 仍为 `change-me` 占位。探针确认 `create_app(env=dev)` 可以启动。这是本地开发默认，Compose 已不再在未设置变量时注入这些值。`MER_ENV=prod` 时占位 `change-me` 会被长度与弱集合拒绝。

### 10.3 M1-009 判定：**关闭**

`update_point` 在 `id` 与路径不一致时抛 `VALIDATION_ERROR`，其余字段 `model_dump` 后 `Point.model_validate`。`test_point_patch_rejects_id_change`：改 `id` 为 422，改名后 `id` 仍为 `P1`。探针：`{"id":"P-EVIL"}` 为 422；`{"id":"P1","name":"同id"}` 为 200 且 `id` 保持 `P1`；`pose` 对象经校验后为 `Pose`（含默认 `theta`）。

### 10.4 不阻挡门禁的残留

| ID | 级别 | 说明 |
|----|------|------|
| M1-006 | P2 | `doc/test.md` 已把一轮 22 passed 记在 Reviewer_Delta，二轮 24 passed 记在 Dev_Max。本二轮复跑记录在本文件，未改 `doc/test.md` |
| M1-007 | P2 | 调度状态机仍属 M2 |
| M1-008 | P2 | 仍无版本化 OpenAPI 快照；`/api/v1/ws` 仍不在 OpenAPI paths |
| M1-010 | P2 | 非法 `pose`（如字符串）使 `Point.model_validate` 的 `ValidationError` 未转成领域错误。探针在 `raise_server_exceptions=False` 下得到 **HTTP 500**。部分更新 `{"pose":{"x":3,"y":4}}` 会整段替换 `pose`，原 `map_id=map-01` 变为 `null`。建议 M2 早期把校验失败映射为 422，并对嵌套字段做合并 |
| M1-011 | P2 | CI backend job 的 `working-directory` 为 `backend`。在该目录执行 `git grep … -- deploy` 找不到仓库根的 `deploy/docker-compose.yml`（退出码 1，被 `!` 当成成功）。无路径限定的 `git grep` 也只搜到 `backend/` 下文件。Compose 回归目前靠 `test_compose_requires_secrets`，不靠该 grep 步骤 |

### 10.5 二轮结论

**通过。M1-002 关闭。建议进入 M2。**

P1（M1-001 / M1-002 / M1-003）均已关闭。M1 门禁可以宣告完成，并开始 M2（优先 M1-007：状态机与 ElevatorAdapter 编排，TC-MVP-11/12）。M1-010、M1-011 可在 M2 开工时顺手处理，不作为进入条件。

- 审核人：**Reviewer_Delta**
- 日期：**2026-09-25**
