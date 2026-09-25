# 经验教训

| 更新日期 | 2026-09-25 |

## 2026-09-25 M1 开工

- 文档 V0.4 已把电梯边界、目录权威、里程碑权威写清；编码前先对齐 scheme §4.2 与 DS §4.1，避免再出现顶层 `adapters/` 分叉。
- 真实设备 API 未到时，Factory **装配期拒绝** vendor 占位，比运行期 NotImplemented 更早失败，CI 不会误连真机。
- `access_mode=via_edge_agent` 同样装配拒绝，防止 MVP 被做成双模对等。
- 审核必须由**实现者以外的 AGENT** 出具独立审核文件，再决定整改或继续。
- AGENTS.md 技术说明路径为 `doc/techical_manual.md`（历史拼写），后续勿另建 `technical_manual.md` 造成双文件。
