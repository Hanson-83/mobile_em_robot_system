# MER Backend（M1）

API Gateway + 领域服务骨架。设备经适配层 Fake 冒烟；真机适配器为占位。

```bash
cd backend
uv sync --extra dev   # 或: pip install -e ".[dev]"
uv run pytest
uv run uvicorn app.main:app --reload --app-dir .
```

环境变量见仓库根 `deploy/.env.example`。设备配置见 `config/devices.example.yaml`。
