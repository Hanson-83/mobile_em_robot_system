# 移动环境监测机器人 — 上位机软件

服务器 + Vue Web 客户端。硬件选型与真机由用户负责；开发与 CI 以 **Fake** 为主路径。

## 当前阶段

- **M0** 文档基线 V0.4：Reviewer_Max 复审通过（plan 有条件通过，条件为初始化 `doc/test.md`，已完成）。
- **M1** 契约与骨架：进行中（本仓库已落地 Fake + Gateway 草图）。

文档入口：`doc/spec/urs.md`、`doc/spec/ds.md`、`ref/project_scheme.md`、`ref/plan.md`。  
待确认项：`ref/pending_confirmations.md`。运行说明：`doc/technical_manual.md`。

## 快速开始

```bash
# 后端
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/uvicorn app.main:app --reload --port 8000

# 前端（另开终端）
cd frontend
npm install && npm run dev
```

开发登录：`admin` / `admin`（仅本地 Fake，勿用于生产）。

## 目录

对齐 `ref/project_scheme.md` §4.2：`backend/app/adapters/`（含 ElevatorFake）、`frontend/`、`config/`、`deploy/`。
