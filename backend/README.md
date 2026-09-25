# mer-host（上位机后端）

API Gateway + 领域服务 + 设备适配层（含 Fake）。目录权威见 `ref/project_scheme.md` §4.2。

## 本地运行

```bash
# 在仓库根目录
python3 -m pip install -e "backend[dev]"
export MER_DEVICES_PATH=config/devices.example.yaml
export MER_FEATURES_PATH=config/features.example.yaml
export MER_JWT_SECRET=dev-only-change-me
uvicorn app.main:app --app-dir backend --reload --port 8000
```

- OpenAPI：http://127.0.0.1:8000/docs
- 存活：`GET /health`  就绪：`GET /ready`

## 测试

```bash
cd backend && python3 -m pytest
```

## 说明

真实 AMR / 仪表 / 电梯适配器（`*_vendor_x`）为占位，待用户提供设备 API 文档后实现。MVP 主路径为 Fake。
