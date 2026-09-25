# DS 审核整改说明（2026-09-25）

| 项 | 内容 |
|----|------|
| 对象 | `doc/spec/ds.md` V0.4 |
| 依据 | `doc/spec/review/review_ds_260925.md` |
| 作者 | PM_Max |

## 已关闭

| 审核 ID | 级别 | 落点 |
|---------|------|------|
| DS-001 | P0 | §4.1 ElevatorAdapter 独立；AmrAdapter 移除电梯方法；§7 Factory；架构图 |
| DS-002 | P0 | **附录 A** URS Must→模块/接口/实体（45 条全覆盖） |
| DS-003 | P1 | §11 可观测性专节 |
| DS-004 | P1 | §4.1.1 RobotStatus 强制字段 + Fake 注入 + 急停中断 |
| DS-005 | P1 | §6.1 任务状态迁移表；§6.2 ApprovalRequest 状态机 + 旁路 |
| DS-006 | P1 | §4.2 MVP 最小 API 资源表 + 错误码初稿 |
| DS-007 | P1 | §5.1 idempotency_key 规则 |
| DS-008 | P1 | §10.1 报警 WebSocket + 权限码 |
| DS-009 | P1 | §10.2 备份范围冻结 + TC-MVP-09 |
| DS-010 | P2 | §13 目录引用 scheme §4.2；删除顶层 adapters/ |
| DS-011 | P2 | §4.3 锁定 WebSocket |
| DS-012 | P2 | §14 三张 mermaid 时序 |
| DS-013 | P2 | §5.2 时序库决策门槛 |

## 仍开放（轻微 TBD）

- 地图中间表示标准化细节
- PDF 引擎选型（HTML 已默认）
- 密码/会话具体数值（配置占位已有）
- URS-NFR-002 恢复实现细节（有 TC-MVP-23）
- URS-ROB-003 低电量阈值默认值

## 建议

请 Reviewer_Max 对 V0.4 做差分复审，重点核对 DS-001/002 与 plan/scheme 交叉一致性。
