# gate-checklist.md — 迭代 9 · 修复切片 2 放行清单

> 当前阶段：迭代 9 · 修复切片 2（命令组合与模式互斥）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `/skill` 与 `/goal`/`/plan`/`/chat` 任意顺序组合；`/goal` 与 `/plan` 互斥取先出现者
- [x] 技能栏点选可追加到已有命令输入；浮层支持非开头 `/skill` 位置
- [x] `pytest -q`（146）、`node --check`、无头垫片、真实服务冒烟

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 9 修复切片 2 条目
- 代码：`agent/web.py`（parseCommand/sendTask/浮层/点选）

## 退出决定

- 通过 → 迭代 9 修复完成
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
