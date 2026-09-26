# 进度状态 — 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 更新日期 | 2026-09-26 |
| 当前阶段 | M5 Gateway / OpenAPI 稳定版 |
| 状态 | Reviewer_API 复审通过；OpenAPI 1.0.0 可冻结 |

## 已完成

- [x] M0 文档基线 V0.4 复审
- [x] M1 契约与骨架（Fake、Gateway、Vue 壳）
- [x] 用户确认写入 `ref/decisions_260926.md`
- [x] M2：任务状态机、排队互斥、电梯技能、断线重连、超限报警、HTML 报告、SQLite
- [x] M3：点位 CRUD、限值、趋势查询、签名批准流、审计只追加、备份恢复
- [x] M4：Vue 页面清单 + 浏览器走通 + Reviewer_UI / Reviewer_Walk 通过
- [x] M5：OpenAPI 1.0.0 + MES 门面 + Reviewer_API / Recheck 通过

## 进行中

- （无）

## 未开始 / 分期

- 桌面/移动客户端（M5+ 分期，本轮明确不交付）
- 真机联调（M6，用户环境）

## 后续行动

1. 用户提供 Modbus 寄存器表与 AMR API 后替换模拟传输
2. 真机联调由用户在现场执行并回填 `doc/test.md`
3. 桌面/移动客户端需单独立项后再排期
