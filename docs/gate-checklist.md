# gate-checklist.md — 迭代 4 · 切片 4.1 放行清单

> 当前阶段：迭代 4 · 切片 4.1（猜你想问）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `suggest_followups` 复用 client 调一次模型（无工具）返回建议
- [x] `--suggest` 在单次任务后输出后续问题建议
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 4 切片 4.1 条目
- 代码：`agent/suggest.py`、`agent/cli.py`、`tests/test_suggest.py`

## 退出决定

- 通过 → 切片 4.2（流式输出）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
