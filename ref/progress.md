# 进度状态 — 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 更新日期 | 2026-09-25 |
| 当前阶段 | M1 契约与骨架（P0a） |
| 状态 | M0 复审关闭；M1 代码已开工，待代码审核 |

## 已完成

- [x] URS/DS/方案/计划 V0.1 → V0.4
- [x] Reviewer_Max 初审 + V0.4 整改 + **V0.4 复审**（DS/scheme **通过**；plan **有条件通过**，条件 T-010 已做）
- [x] M1 仓库骨架（scheme §4.2）
- [x] 适配接口 + Fake（Amr/Elevator/Particle/Climate/Airflow）+ Vendor 占位
- [x] Gateway/OpenAPI 草图、鉴权、错误体、健康检查
- [x] Fake 冒烟（含电梯 Call/Enter/Exit）+ pytest 11 通过
- [x] Vue 骨架（登录/地图壳/任务列表）
- [x] `doc/test.md` 初始化

## 进行中

- [ ] M1 代码审核（独立 AGENT）与整改
- [ ] OpenAPI 草图与 DS 资源表剩余路径（报警 ack/close、报告、用户、批准）占位补齐

## 未开始（后续）

- M2 编排状态机 + 互斥 queue + 持久化（P0b 深化）
- M3 批准流 / 备份 / RBAC 细表
- 真机联调（用户环境，M6）

## 跟踪文档

- `ref/tasks.md`、`ref/risks.md`、`ref/pending_confirmations.md`
- `doc/test.md`、`doc/technical_manual.md`

## 后续行动

1. 按代码审核整改 M1
2. 进入 M2 调度状态机（仍 Fake）
3. 用户补充 Q-01..Q-14 后替换 VendorStub
