# 技术方案（project_scheme）V0.4 差分复审意见（2026-09-25）

## 1. 审核元信息

- 审核对象：`ref/project_scheme.md` V0.4 / MER-SCHEME-001
- 审核类型：整改后差分复审（对照 `ref/review/review_project_scheme_260925.md` 与 `ref/review/remediation_note_260925.md`）
- 审核依据：`AGENTS.md`、`ref/requirement.md`、`doc/spec/urs.md` V0.3、`doc/spec/ds.md` V0.4、`ref/plan.md` V0.4；工程规范全套
- 审核人：Reviewer_Max
- 审核日期：2026-09-25
- 总体结论：**通过** — P0（SCH-001/002）与整改所列 P1/P2 已落盘；§9 与 plan §1.2 里程碑 ID/名称逐字一致；`elevators[]` + 独立 ElevatorAdapter 可指导脚手架与 Fake 装配。

## 2. 差分复审说明

| 审核 ID | 级别 | 复审结论 | 验证要点（V0.4 落点） |
|---------|------|----------|------------------------|
| SCH-001 | P0 | **已关闭** | §9 表 M0–M7 与 plan §1.2 **编号与名称逐字一致**；权威声明指向 plan §1.2 |
| SCH-002 | P0 | **已关闭** | §4.4 `elevators[]` + `elevator_fake`；§2/§4.3/§5 独立 **ElevatorAdapter**；与 DS §4.1 一致 |
| SCH-003 | P1 | **已关闭** | §5.1 资源锁（类型、TTL、冲突策略、2 机伪流程） |
| SCH-004 | P1 | **已关闭** | §6.1 续传幂等键、重试责任（适配层/数据服务） |
| SCH-005 | P1 | **已关闭** | §8.2 日志与健康检查；引用 observability |
| SCH-006 | P1 | **已关闭** | §4.3.1 Bearer/限流/权限映射/v2 策略 |
| SCH-007 | P1 | **已关闭** | §4.2 目录权威声明（`backend/app/adapters/`） |
| SCH-008 | P1 | **已关闭** | §8.1 部署安全清单（内网 HTTP + 强制鉴权等） |
| SCH-009 | P2 | **已关闭** | §6 导出默认 CSV；报告 HTML 优先 |
| SCH-010 | P2 | **已关闭** | §9 按里程碑拆分，无 M4/M5 合并歧义表述 |
| SCH-011 | P2 | **已关闭** | §3.3 Measurement `quality` 枚举与失败落数策略 |

## 3. 符合项

- §9 仅补充「软件交付物」，未再定义与 plan 冲突的里程碑语义 — SCH-001 根治 V0.3 双源真相问题。
- 外部系统表明确 AMR **不含**电梯方法，电梯走 ElevatorAdapter — 与 DS、URS-ROB-007 一致。
- `devices.example.yaml` 含 `elevators[]`、`elevator_skills`、`resource_mutex: simple`、`realtime_channel: websocket` — 可直接作 M1 配置 schema 起点。
- §10 开放问题收敛为轻微 TBD，阻塞项已关闭清单与 URS §7 决策一致。

## 4. 问题清单（残留 / 观察项）

| ID | 严重级别 | 位置 | 问题描述 | 建议 |
|----|----------|------|----------|------|
| SCH-R01 | P2 | §5 地图 | 地图中间表示标准化仍为轻微 TBD（与 DS URS-SCH-005 一致） | M2 地图页开发前与 AMR 厂工具格式对齐纪要 |
| SCH-R02 | P2 | §8 备份 | 备份作业调度（cron/timer）频率未写死 | M3 与 TC-MVP-09 脚本一并交付运维说明 |
| SCH-R03 | P2 | §4.3.1 限流 | MVP 限流默认值为「可配置」叙述，无数值示例 | M1 Gateway 实现时给默认值并写入 OpenAPI 旁注 |
| SCH-R04 | P2 | 文档头 | `状态: Draft` | M0 收口时升 Baseline |

**无未关闭 P0；无未关闭上一轮关键 P1。**

## 5. 需求追溯（方案层）

- V0.3 审核 §5 缺口：资源锁（SCH-003）、幂等（SCH-004）、Gateway 细节（SCH-006）、部署安全（SCH-008）、Vue 页面（plan §3.1 承接 CLI-001）— 方案+plan 联合已覆盖。
- 批准流仍「见 DS」— DS §6.2 已细化，方案层引用足够用于 M1 脚手架。

## 6. 与其他文档一致性

| 维度 | 结论 |
|------|------|
| plan §1.2 ↔ scheme §9 里程碑 | **逐字对齐**（人工核对 M0–M7 共 8 行） |
| DS §4.1 ElevatorAdapter | 一致 |
| DS §13 目录 | scheme §4.2 为权威 — 一致 |
| plan WBS Fake 清单 | §4.4 `elevator_fake` — 一致 |

## 7. 结论与建议

- **总体结论：通过。**
- 建议将 `project_scheme.md` V0.4 作为 **monorepo 目录与部署/配置的唯一布局权威**，与 DS/plan 一并冻结 M0。

## 8. 后续验证关注点

- 脚手架 `backend/app/adapters/` 是否含 `elevator/fake` 模块且 Factory 可装配。
- §5.1 资源锁 TTL/等待超时是否在集成测试（TC-MVP-12）可配置验证。
- 里程碑结束时执行 plan §7「文档漂移」核对：scheme §9 第三列可增细节但不得改 ID/名称。
