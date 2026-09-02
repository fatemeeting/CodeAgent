# gate-checklist.md — 迭代 10 · 切片 10.1 放行清单

> 当前阶段：迭代 10 · 切片 10.1（/plan 两段式人工确认）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] Web `/plan` 两段式：pending 计划暂停不执行；✓确认 / ✎修改 / ✕取消；重放可恢复
- [x] 确认 → plan_text 注入执行；修改 → plan_feedback 重新生成；取消不执行；生成失败降级
- [x] CLI `--plan` 交互确认（y/n/修改意见）；非交互取消
- [x] `pytest -q` 全绿（153）、`compileall`、`node --check`、无头垫片、真实冒烟

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 10 切片 10.1 条目
- 代码：`agent/plan.py`、`agent/web.py`、`agent/cli.py`、`tests/test_plan.py`、`tests/test_web.py`

## 退出决定

- 通过 → 切片 10.2（或迭代 10 其余需求）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
