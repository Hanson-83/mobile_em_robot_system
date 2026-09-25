# 移动环境监测机器人上位机

上位机（API Gateway + Vue Web）用于编排监测机器人到点采样，保存粒子 / 温湿度 / 风速数据，并提供报警、批报告、权限和可开关的审计 / 批准流。

硬件选型、真机与电梯协议由用户负责。当前主路径是 Fake 适配器，不依赖真机即可开发和验收软件。

## 目录

| 路径 | 说明 |
|------|------|
| `backend/` | FastAPI Gateway、调度、适配层、仓储 |
| `frontend/` | Vue 3 Web，只调用 Gateway |
| `config/` | 设备与功能开关示例 |
| `deploy/` | Docker Compose 与 PostgreSQL 分区 / 备份说明 |
| `doc/spec/` | URS / DS |
| `ref/` | 需求、方案、计划、进度 |

## 本地运行

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

cd ../frontend
npm ci
npm run dev
```

浏览器打开 `http://127.0.0.1:5173`。开发种子账号（仅 `MER_DEV_SEED=true` 时创建）：

| 账号 | 口令 | 角色 |
|------|------|------|
| admin | Admin123! | 管理 |
| operator | Operator1! | 操作 |
| viewer | Viewer123! | 查看 |

开发 API Token：`dev-api-token-change-me`。生产必须设置 `MER_DEV_SEED=false`、`MER_ALLOW_DEV_SECRET=false`，并更换 `MER_SECRET_KEY`。

## 检查

```bash
cd backend && uv run ruff check app tests && uv run pytest
cd frontend && npm run typecheck && npm run build
```

## 部署

见 `deploy/docker-compose.yml` 与 `doc/techical_manual.md`。默认内网 HTTP + 强制鉴权。现场若不能接受明文 HTTP，需自行加 TLS。
