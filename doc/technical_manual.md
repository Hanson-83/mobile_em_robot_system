# 技术说明 — 上位机 M1 契约与骨架

| 项 | 内容 |
|----|------|
| 日期 | 2026-09-25 |
| 阶段 | M1（契约与骨架） |
| 目录权威 | `ref/project_scheme.md` §4.2 |

## 1. 方案要点

- 单体模块化：FastAPI 进程内同时承担 **API Gateway** 与领域服务（M1）。
- 对内设备经 `backend/app/adapters/`；**ElevatorAdapter 独立**；AmrFake **无**电梯方法。
- Fake 一等公民；`amr_vendor_x` / `elevator_vendor_x` 等为 **NOT_IMPLEMENTED 占位**，待用户 API。
- MVP `access_mode` 仅 `direct`；`via_edge_agent` 工厂拒绝。
- 默认 `features.e_sign=false`；签名批准流占位到 M3。
- 前端 Vue 3 仅调 Gateway；实时通道 WebSocket 握手占位。

## 2. 仓库与运行

```text
backend/app/{api,domain,adapters,services,core}
frontend/src
config/devices.example.yaml
deploy/docker-compose.yml
```

后端：

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：`cd frontend && npm install && npm run dev`（代理 `/api` → `:8000`）。

开发账号（仅 Fake/CI）：`admin/admin`、`operator/operator`。密钥走 `MER_SECRET`。

## 3. 适配器切换

改 `config/devices.example.yaml` 的 `adapter` 字段即可（`amr_fake` → `amr_vendor_x`）。厂商实现补齐前调用将返回 `NOT_IMPLEMENTED`。

## 4. M2 调度（2026-09-26）

用户确认见 `ref/decisions_260926.md`。

- 任务：`Created → Queued → Dispatched → Running → Succeeded|Failed|Cancelled`
- 冲突默认 `queue`：电梯锁先于点位锁
- 断线默认重连 3 次
- 粒子通道 0.1/0.5/1.0/5.0 µm；温湿度 ℃/%；风速 m/s；经 Modbus 保持寄存器模拟
- 地图：GeoJSON FeatureCollection 导入
- 报告：`var/reports/*.html`（或 `MER_REPORT_DIR`）
- 库：`MER_SQLITE`（默认 `var/mer.sqlite`）

开发环境变量与 M1 相同。创建任务默认 `auto_start=true`，资源被占时保持 `Queued`，`POST /tasks/{id}/start` 继续。

## 5. M3 合规（2026-09-26）

- `e_sign=false`：`PATCH /api/v1/settings/limits` 直接生效。
- `e_sign=true`：同一接口返回 `APPROVAL_REQUIRED`，由另一用户 `POST /api/v1/approvals/{id}/decide` 带口令签署。发起人不能自批。默认 72 小时过期。
- `audit_trail=true` 时关键动作写入 `audit_events`，应用层拒绝删除。
- 备份：`POST /api/v1/admin/backup` 与 `restore`。范围是 SQLite、`config/` 下 YAML/GeoJSON、报告目录。恢复前核对数据库 SHA256。
- 趋势：`GET /api/v1/trends?metric=0.5um`。

## 6. M4 Vue 页面（2026-09-26）

`cd frontend && npm install && npm run dev`，浏览器打开 `http://localhost:5173`。开发代理把 `/api` 转到 `http://localhost:8000`。

页面：登录、地图监控、任务编排、点位/限值、实时趋势、报警、报告、用户权限、系统开关、批准中心。报告页从任务下拉选择，避免手抄 ID。



