# 进度状态 — 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 更新日期 | 2026-09-26 |
| 当前阶段 | M5 Gateway / OpenAPI 稳定版 |
| 状态 | OpenAPI 1.0.0 + MES 门面已实现，待独立审核 |

## 已完成

- [x] M0 文档基线 V0.4 复审
- [x] M1 契约与骨架（Fake、Gateway、Vue 壳）
- [x] 用户确认写入 `ref/decisions_260926.md`
- [x] M2：任务状态机、排队互斥、电梯技能、断线重连、超限报警、HTML 报告、SQLite
- [x] M3：点位 CRUD、限值、趋势查询、签名批准流、审计只追加、备份恢复
- [x] M4：Vue 页面清单 + 浏览器走通 + Reviewer_UI / Reviewer_Walk 通过
- [x] M5 实现：OpenAPI stable 1.0.0；`/api/v1/integrations/mes/*`；服务账号 Token；契约测试

## 进行中

- [ ] M5 独立 AGENT 审核与整改

## 未开始 / 分期

- 桌面/移动客户端（M5+ 分期，本轮明确不交付）
- 真机联调（M6，用户环境）

## 后续行动

1. 审核 M5，按意见整改后冻结契约
2. 用户提供 Modbus 寄存器表与 AMR API 后替换模拟传输
3. 真机联调由用户在现场执行并回填 `doc/test.md`
