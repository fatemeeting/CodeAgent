# gate-checklist.md — 迭代 9 · 切片 9.5 放行清单

> 当前阶段：迭代 9 · 切片 9.5（集成回归）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 全量回归：`pytest -q`（146）、compileall、--help、REPL /quit、CLI --list-skills/--skill
- [x] 前端回归：node --check + 无头 DOM 垫片（技能装载块/面板 CRUD/命令）
- [x] 真实冒烟：显式 /skill + chat 共存（chat 仅装载 modes 含 chat、agent-only 过滤、未指定不装载）；会话与技能 CRUD 共存
- [x] 证据入 AGENT_LOG，迭代 9 放行

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 9 切片 9.5 条目
- 代码：本轮仅契约文件与日志（无代码改动，除非回归失败最小修复）

## 退出决定

- 通过 → 迭代 9 放行，进入下一迭代
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
