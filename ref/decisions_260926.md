# 用户确认记录（2026-09-26）

| 项 | 决定 | 实现 |
|----|------|------|
| AMR 契约 | 仍不确定 | 继续 AmrFake / 厂商占位，按导航、状态、急停的常规语义模拟 |
| 电梯 | 不经 AMR 聚合 | 保持独立 ElevatorAdapter；协议与寄存器仍为模拟 |
| 粒子通道 | 0.1 / 0.5 / 1.0 / 5.0 µm | ParticleFake 四通道；计数单位 count/cf |
| 温湿度 | ℃ 与 % | ClimateFake；Modbus 占位为温度×10、湿度×10 |
| 风速 | m/s | AirflowFake；Modbus 占位为风速×100 |
| 仪表协议 | Modbus | `ModbusHoldingSim` 占位，寄存器表待厂商表替换 |
| 地图 | 不确定 | 先按常见 GeoJSON Point 导入；ROS yaml+pgm 未解析 |
| 现场传输 | 内网 HTTP | 维持强制鉴权，不启用 TLS |
| 对外常规操作 | 任务下发、启停、状态与实时数据 | `POST /tasks`、`/start`、`/stop`、`GET /tasks`、`GET /realtime` |
| 资源冲突 | 默认排队 | `on_conflict=queue` |
| 断线 | 默认重连 | `session_on_disconnect=reconnect`，默认 3 次，仍失败则任务 Failed |
| 其余 | 按易实现推荐 | SQLite 持久化；超限报警可确认；任务 HTML 批报告；进程中断的 Running 记 PROCESS_LOST |

仍开放：生产用户目录、PDF 引擎、时序库触发、低电量阈值、时区、充电桩 ID 规则、真机寄存器表。
