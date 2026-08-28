# gate-checklist.md — 迭代 2 · 切片 2.1 放行清单

> 当前阶段：迭代 2 · 切片 2.1（多轮 REPL）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 无任务参数启动进入 REPL；`/quit` `/clear` `/history` `/help` 生效
- [x] 多轮对话跨轮保留历史（第 2 轮能理解「刚才」）
- [x] 单次任务模式 `python -m agent "任务"` 不回归
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 2 切片 2.1 条目
- 代码：`agent/repl.py`、`agent/loop.py`、`agent/cli.py`、`tests/test_repl.py`

## 退出决定

- 通过 → 切片 2.2（会话持久化）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
