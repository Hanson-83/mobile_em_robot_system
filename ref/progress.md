# 进度状态 — 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 更新日期 | 2026-09-25 |
| 当前阶段 | **M1 契约与骨架（进行中）** |
| 状态 | 用户要求启动开发；V0.4 文档作为工作基线推进 P0a |

## 已完成

- [x] URS/DS/方案/计划 V0.1 → V0.4（文档基线）
- [x] Reviewer_Max 三份审核 + V0.4 整改写回
- [x] **M1 代码骨架落地（本轮）**：scheme §4.2 目录；适配接口 + Fake（含 ElevatorFake）；Gateway/OpenAPI 草图；Vue 登录/地图壳/任务列表；`doc/test.md` 模板

## 进行中

- [ ] M1 本地/CI 测试与独立 AGENT 审核
- [ ] 按审核结果整改或宣布 M1 门禁通过

## 未开始

- M2：编排状态机 + 简单互斥排队 + 电梯技能全链路
- M3：PG、RBAC 完善、批准流细表、备份
- M4：Vue MVP 页面闭环
- M6：真机联调（用户执行）

## 跟踪文档

- `ref/tasks.md`
- `ref/risks.md`
- `ref/open_confirmations.md` — **请用户确认**
- `doc/test.md`

## 后续行动

1. 跑通 pytest / 前端 typecheck+build
2. 分配独立审核 AGENT，生成 `ref/review/review_M1_260925.md`
3. 按审核整改或进入 M2
4. 用户确认 `ref/open_confirmations.md` 中 Q-01..Q-12（不阻塞 Fake）
