# gate-checklist.md — 迭代 5 · 切片 5.2 放行清单

> 当前阶段：迭代 5 · 切片 5.2（并行工具调用）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 多个 tool_calls 并发执行（ThreadPoolExecutor）
- [x] 观测按调用顺序回填（tool_call_id 顺序一致）
- [x] 单个 tool_call 行为不变（不回归）
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 5 切片 5.2 条目
- 代码：`agent/loop.py`、`tests/test_loop.py`

## 退出决定

- 通过 → 切片 5.3（human-in-the-loop）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
