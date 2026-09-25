# 经验教训

| 日期 | 主题 | 经验 |
|------|------|------|
| 2026-09-25 | 文档双源里程碑 | 必须声明单一权威（plan §1.2），scheme 只对齐编号名称，否则排期误读。 |
| 2026-09-25 | 电梯边界 | AmrAdapter 与 ElevatorAdapter 必须拆开；否则 Fake、YAML、URS-ROB-007 无法编码。 |
| 2026-09-25 | 无 python3-venv | 本环境需先安装 `python3.12-venv` 才能创建 `.venv`；记录以免重复踩坑。 |
| 2026-09-25 | 真机资料不全 | 用 Fake + VendorStub(NOT_IMPLEMENTED) 不阻塞 M1；待确认项集中在 pending_confirmations。 |
