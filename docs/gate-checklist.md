# gate-checklist.md — 迭代 4 · 切片 4.2 放行清单

> 当前阶段：迭代 4 · 切片 4.2（流式输出）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `chat_stream` 逐 token 打印内容并重建 tool_calls（等价响应）
- [x] `--stream` 最终答复流式输出，不重复打印
- [x] 未开启 stream 时行为不变（不回归）
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 4 切片 4.2 条目
- 代码：`agent/llm.py`、`agent/loop.py`、`agent/cli.py`、`agent/repl.py`

## 退出决定

- 通过 → 迭代 4 完成
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
