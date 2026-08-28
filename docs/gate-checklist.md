# gate-checklist.md — 迭代 3 · 切片 3.1 放行清单

> 当前阶段：迭代 3 · 切片 3.1（token / 费用统计）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `LLMClient` 累计 prompt / completion tokens（mock 可测）
- [x] 单次任务 `--usage` 输出用量 + 估算费用
- [x] REPL `/usage` 输出累计用量
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 3 切片 3.1 条目
- 代码：`agent/llm.py`、`agent/loop.py`、`agent/cli.py`、`agent/repl.py`、`tests/test_llm.py`

## 退出决定

- 通过 → 切片 3.2（自我反思）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
