# gate-checklist.md — 迭代 8 · 切片 8.4 放行清单

> 当前阶段：迭代 8 · 切片 8.4（上下文压缩 compaction）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `_maybe_compact`：≥80% 预算 + >8 条时触发；旧轮次 LLM 总结 ≤300 字；替换为 `[上下文压缩摘要]`；`compact {before, after, summary}` 事件；失败回退旧截断
- [x] 仅 Web（emit 非空）启用，CLI 零回归（emit None 不触发额外 LLM 调用）
- [x] 前端「📦 上下文压缩」折叠块（before → after tokens + 摘要正文）
- [x] `pytest -q` 全绿（123）；`node --check`；DOM 垫片；冒烟标记

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 8 切片 8.4 条目
- 代码：`agent/loop.py`、`agent/web.py`、`tests/test_loop.py`

## 退出决定

- 通过 → 切片 8.5（集成回归，迭代 8 收尾）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
