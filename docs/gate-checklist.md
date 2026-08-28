# gate-checklist.md — 迭代 6 · 切片 6.2 放行清单

> 当前阶段：迭代 6 · 切片 6.2（SSE 流式推送）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `/events` 以 SSE 逐条推送过程与最终答复（[DONE] 结束）
- [x] 前端 EventSource 实时追加显示
- [x] `/` 与 `/run` 行为不变（不回归）
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 6 切片 6.2 条目
- 代码：`agent/web.py`、`tests/test_web.py`

## 退出决定

- 通过 → 迭代 6 完成
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
