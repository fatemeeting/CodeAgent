# gate-checklist.md — 迭代 5 · 切片 5.1 放行清单

> 当前阶段：迭代 5 · 切片 5.1（任务规划 plan-first）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `make_plan` 复用 client 调一次模型（无工具）返回分步计划
- [x] `--plan` 执行前打印计划并注入执行上下文
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 5 切片 5.1 条目
- 代码：`agent/plan.py`、`agent/cli.py`、`tests/test_plan.py`

## 退出决定

- 通过 → 切片 5.2（并行工具调用）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
