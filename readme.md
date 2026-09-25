# 移动环境监测机器人上位机

上位机（服务器 + Vue Web 客户端）系统。硬件选型与真机联调由用户负责；软件主路径以 Fake/Simulator 验收。

## 文档

| 文档 | 路径 |
|------|------|
| 需求 | `ref/requirement.md` |
| URS | `doc/spec/urs.md` |
| 设计规范 | `doc/spec/ds.md` |
| 技术方案 | `ref/project_scheme.md` |
| 规划 | `ref/plan.md` |
| 进度 | `ref/progress.md` |
| 待确认项 | `ref/open_confirmations.md` |

## 仓库布局（scheme §4.2）

```text
backend/app/{api,domain,adapters,services,core}
frontend/src
config/{devices,features}.example.yaml
deploy/{docker-compose.yml,.env.example}
```

## 快速启动（开发）

```bash
# 后端
python3 -m pip install -e "backend[dev]"
export MER_REPO_ROOT=.
export MER_JWT_SECRET=dev-only-change-me
uvicorn app.main:app --app-dir backend --port 8000

# 前端
cd frontend && npm install && npm run dev
```

默认开发账号：`admin` / `admin`（部署时通过环境变量覆盖）。

OpenAPI：http://127.0.0.1:8000/docs

## 测试

```bash
cd backend && python3 -m pytest
cd frontend && npm run typecheck && npm run build
```

真机 / HIL 测试不在 CI 中执行，由用户在现场环境反馈。
