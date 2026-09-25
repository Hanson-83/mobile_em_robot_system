# 技术说明 — M1 契约与骨架

| 项 | 内容 |
|----|------|
| 阶段 | M1 契约与骨架 |
| 日期 | 2026-09-25 |
| 作者 | Dev_Max |

## 方案要点

- 单体模块化：FastAPI Gateway 与领域服务同进程；设备经 `backend/app/adapters/`。
- **ElevatorAdapter 独立**，AmrAdapter 不含电梯方法。
- MVP `access_mode=direct`；`via_edge_agent` 装配即拒绝（演进占位）。
- 真实厂商适配器 `*_vendor_x` 装配即拒绝，待用户 API 文档。
- 前端 Vue 3 + Vite；经 Gateway；实时通道预留 WebSocket 握手。
- 数据仓储 M1 为内存；M3 换 PostgreSQL。

## 关键实现

| 模块 | 路径 | 说明 |
|------|------|------|
| Gateway | `backend/app/main.py` `api/routes.py` | `/api/v1` 资源表 + `/health` `/ready` |
| 错误模型 | `backend/app/core/errors.py` | `{code,message,retryable}` |
| Fake | `adapters/*/fake.py` | 含急停/电梯失败注入 |
| Factory | `adapters/factory.py` | YAML 装配 |
| 资源锁 | `services/lock.py` | 简单互斥；queue 在 M1 进程内仍返回冲突（排队在 M2） |
| 幂等 | `services/idempotency.py` | `client_request_id` 或 sha1 |

## 启动与迁移

1. Python 3.11+，`pip install -e backend[dev]`。
2. 配置：`config/devices.example.yaml`、`config/features.example.yaml`。
3. 密钥：`deploy/.env.example`，勿入库真实值。
4. 用户补充设备 API 后：新增 `*_vendor_x` 实现并改 YAML `adapter`，不改编排核心。
5. 真机联调：用户现场执行，回填 `doc/test.md`。

## M2 进展

- `backend/app/services/scheduler.py`：Created→Queued→Dispatched→Running→终态
- 技能：navigate_to / dock_charge / call|enter|exit_elevator / sample_particle / read_climate / read_airflow
- 电梯：`acquire` → ElevatorAdapter → `release`；失败释放锁
- Gateway：`POST /api/v1/tasks/{id}/start`

## 已知限制

- 资源锁 `queue` 尚未实现等待（冲突立即返回）
- 组合/集群任务未做
- WebSocket 仅订阅确认，无推送循环
- 地图为占位画布
- 内存仓储，杀进程后任务丢失（URS-NFR-002 待 M3）
