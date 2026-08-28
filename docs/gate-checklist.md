# gate-checklist.md — 迭代 3 · 切片 3.2 放行清单

> 当前阶段：迭代 3 · 切片 3.2（自我反思 reflection）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 模型给出答复后注入自检提示（仅一轮）
- [x] 反思发现问题→继续调工具修正；确认完成→返回原答复
- [x] 未开启 reflect 时行为不变（不回归）
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 3 切片 3.2 条目
- 代码：`agent/loop.py`、`agent/config.py`、`agent/cli.py`、`tests/test_loop.py`

## 退出决定

- 通过 → 迭代 3 完成
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
