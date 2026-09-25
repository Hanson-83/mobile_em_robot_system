# 操作日志

| 日期 | 操作者 | 操作摘要 | 路径/对象 | 备注 |
|------|--------|----------|-----------|------|
| 2026-09-25 | PM_Max | 根据 `ref/requirement.md` 与 `spec/*`、他厂参考材料，生成用户需求规范、设计规范、技术方案与项目规划；并写入进度摘要 | 见下方路径列表 | 文档阶段；未改业务源码；未 git clone/push |
| 2026-09-25 | PM_Max | **范围收窄为上位机**：备份四份核心文档后覆盖写 V0.2；更新本日志与 `ref/progress.md` | 见「范围收窄」节 | 硬件选型改由用户负责；不做清洁/不做硬件选型 |

## 2026-09-25 生成路径列表

- `doc/spec/urs.md` — 用户需求规范（URS）
- `doc/spec/ds.md` — 设计规范（DS）
- `ref/project_scheme.md` — 技术方案
- `ref/plan.md` — 规划/计划（含测试方案，引用 project_scheme）
- `ref/progress.md` — 进度状态（文档阶段完成）
- `doc/operation_log.md` — 本操作日志（本条）

生成流程：先在构建机 `/workspace/mer_deliverables/` 撰写 → 拷贝至用户机临时目录 → `Copy-Item` 至项目根 `D:\Projects\mobile_em_robot_system\` 对应路径；验证 UTF-8 与文件存在。

## 2026-09-25 上位机范围收窄

### 变更原因

用户明确：所有硬件设备选型由用户自己做；本次任务与文档仅针对上位机（服务器+客户端）系统开发。

### 备份（同目录，AGENTS.md 命名）

- `doc/spec/urs.md_backup_20260925_上位机范围收窄_01.md`
- `doc/spec/ds.md_backup_20260925_上位机范围收窄_01.md`
- `ref/project_scheme.md_backup_20260925_上位机范围收窄_01.md`
- `ref/plan.md_backup_20260925_上位机范围收窄_01.md`

### 覆盖写回（V0.2）

- `doc/spec/urs.md`
- `doc/spec/ds.md`
- `ref/project_scheme.md`
- `ref/plan.md`
- `ref/progress.md`（更新）
- `doc/operation_log.md`（本追加）

### 流程

1. box `/workspace/mer_host_scope/` 生成新稿  
2. CopyFromBox → `C:\Users\heng.wang\AppData\Local\Temp\mer_host_scope\`  
3. 用户机 Shell：项目内 `Copy-Item` 备份四份核心稿 → 再覆盖新版  
4. UTF-8 无 BOM 校验  

### 风险与回滚

- 风险：覆盖写错范围表述。回滚：用上述 `_backup_20260925_上位机范围收窄_01` 文件 `Copy-Item` 还原。
