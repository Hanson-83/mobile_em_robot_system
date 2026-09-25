# 进度状态 — 移动环境监测机器人上位机软件

| 项 | 内容 |
|----|------|
| 更新日期 | 2026-09-25 |
| 当前阶段 | **M1 已通过；M2 调度 MVP 已开工** |
| 状态 | Reviewer_QA 有条件通过 → Reviewer_Delta 二轮复审 **通过**（M1-002 关闭）；M2 状态机+电梯 Fake 全链路冒烟已落地 |

## 已完成

- [x] 文档 V0.4 作为开发工作基线
- [x] M1 契约与骨架（目录 / Fake / Gateway / Vue 壳）
- [x] Reviewer_QA 初审 + Reviewer_Delta 差分复审（通过）
- [x] M1 P1 整改（路由、限流、密钥门禁、Compose 必填、CI 扫描）

## 进行中

- [ ] M2：编排状态机已有第一片（电梯 Call/Enter/Exit + 采样入库 + 急停失败）；互斥排队、组合任务仍待补
- [ ] M2 完成后分配独立 AGENT 审核

## 未开始

- M3 数据与合规（PG、批准流细表、备份）
- M4 Vue MVP 页面闭环
- M6 真机联调（用户执行）

## 跟踪文档

- `ref/tasks.md`
- `ref/risks.md`
- `ref/open_confirmations.md` — **请确认**
- `doc/test.md`
- `ref/review/review_M1_260925.md`
- `ref/review/review_M1_remediation_260925.md`

## 后续行动

1. 补 M2 资源锁 queue 等待、组合任务、失败回充
2. M2 完成后独立审核
3. 用户确认 `ref/open_confirmations.md`
