# M3 P1 复核意见（2026-09-26）

## 1. 审核元信息

| 项 | 内容 |
|----|------|
| 审核对象 | 原审核 `ref/review/review_M3_260926.md` 的 P1：M3-001、M3-002、M3-003 |
| 仓库 / 分支 | `/workspace` / `cursor/m3-compliance-8317` |
| 对照提交 | 原审核 `471a834`；整改 `2de6ccb`（`fix(m3): 限值落库、禁止点位绕过批准流、恢复后重载`）；复核时 HEAD `94aa236` |
| 阅读范围 | `backend/app/services/compliance.py`、`store.py`；`backend/app/api/routes/compliance.py`；`backend/tests/test_m3_compliance.py`；启动加载核对 `backend/app/main.py` lifespan |
| 审核人 | **Reviewer_Rel** |
| 审核日期 | 2026-09-26 |
| 总体结论 | **通过** |

结论说明：M3-001～M3-003 已闭环。限值在直接生效与批准生效时写入 SQLite `kv`（键 `limits`），进程启动时优先加载该快照；点位 POST/PATCH 携带 `limits` 返回 422；备份恢复覆盖库与配置后重载内存限值与 features。`cd /workspace/backend && .venv/bin/pytest -q`：**36 passed**，1 warning（Starlette/anyio 弃用）。P2（M3-004～M3-010）不在本次关闭范围，按原审核可与 M4 并行，**不再阻塞 M4**。

## 2. 验证结果

| 检查 | 结果 |
|------|------|
| 后端测试：`cd /workspace/backend && .venv/bin/pytest -q` | **通过**：36 passed，1 warning |
| M3 用例文件 | `tests/test_m3_compliance.py` 6 项，含重启加载、点位拒绝 `limits`、恢复后限值回到备份值 |
| 业务代码 | 本次复核只读，未改代码、未 commit |

## 3. P1 逐项

| ID | 原问题 | 复核 | 证据 |
|----|--------|------|------|
| M3-001 | 批准后限值只改进程内 dict，重启回到 YAML | **关闭** | `request_limit_change`（`e_sign=false`）与 `decide_approval`（`Approved` 且 `action==limit.update`）均调用 `commit_limits` → `Store.save_blob("limits", …)`。`lifespan` 在 `build_scheduler` 之后执行 `reload_limits(store, state.limits, scheduler.limits)`：有 blob 则覆盖共享 dict，无 blob 则保留 YAML。`state.limits` 与 `scheduler.limits` 为同一对象。`test_limits_survive_restart_and_point_cannot_bypass`：写入 `temperature_c.max=19` 后新建 `TestClient`（再次走 lifespan、同一 `MER_SQLITE`），GET 仍为 19。 |
| M3-002 | `PATCH /points/{id}` 可直接 `save_point` 改 `limits`，绕过签名 | **关闭** | `create_point` 与 `patch_point` 在写库前若 body 含键 `limits` 则 `VALIDATION_ERROR`（HTTP 422），文案指向 `/api/v1/settings/limits`。PATCH 的拒绝发生在按 id 取点之前。测试在 `e_sign=true` 下对点位提交 `limits`，断言 422。 |
| M3-003 | 恢复覆盖磁盘后内存 `limits`/`features` 不重载 | **关闭** | `POST /admin/restore` 在 `restore_backup` 成功后调用 `reload_limits(store, state.limits, load_limits(config_dir))`，再 `state.features = load_features(config_dir)` 并写回 `scheduler.features`。`restore_from` 会关闭并重开 SQLite 连接，随后 `get_blob` 读到恢复后的库。`test_backup_restore_roundtrip`：备份时 max=21，再改为 99，恢复后 GET 为 21（排除“内存仍为 99”和“只回到 YAML 出厂值”）。 |

## 4. 观察（不升为未关闭 P1）

| 项 | 说明 |
|----|------|
| 落库形态 | 整份快照存 `kv.limits`，不回写 `limits.example.yaml`，也无逐次版本行。启动以 blob 优先、YAML 为缺省。满足 DS §6.2「限值变更落库」及原建议中的持久化并启动加载。 |
| 重启用例路径 | 重启断言走的是 `e_sign=false` 直接生效。批准路径使用同一 `commit_limits`，未再单开「批准后再启进程」用例。 |
| 点位用例范围 | 自动化覆盖的是 PATCH（目标点可不存在）。POST 有相同守卫，未单独断言。创建点位时写入的 `limits` 恒为空对象，因为含该键会先被拒绝。 |
| features 重载 | 恢复路径调用 `load_features`，用例未单独断言开关值。启动还会把 `devices` YAML 的 `features` 段合并进来；恢复路径不再做这一步。当前 `config/features.example.yaml` 与 `config/devices.example.yaml` 的 `audit_trail`/`e_sign` 均为 false，不产生可见偏差。 |

## 5. 是否还阻塞 M4

| 项 | 结论 |
|----|------|
| M3-001～M3-003 | **已关闭，不再作为进入 M4 的条件** |
| M3-004～M3-010（P2） | 仍开放。原审核允许与 M4 并行或书面豁免，本次不改该安排 |
| 是否还阻塞 M4 | **否** |

---

**返回摘要（给协调方）**

- **结论**：通过
- **P1**：M3-001、M3-002、M3-003 均关闭
- **是否还阻塞 M4**：**否**
