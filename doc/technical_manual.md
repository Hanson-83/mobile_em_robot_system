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

## 4. 已知占位

见 `ref/pending_confirmations.md`。互斥 `queue` 策略、完整任务状态机、持久化 PG、批准流、报表 HTML 均未在 M1 完成。
