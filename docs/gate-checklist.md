# gate-checklist.md — 迭代 8 · 切片 8.3 放行清单

> 当前阶段：迭代 8 · 切片 8.3（subagent 工具）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `delegate_subagent`：短预算 3 轮、不可再委托（工具集排除自身）、stdout 静默、摘要回填；缺 task/配置缺失报错；注册进工具表（9 工具）
- [x] `run(tools=)` 可选参数；loop 发 subagent_start/subagent_end 事件；SYSTEM_PROMPT 提及
- [x] 前端「🤖 子代理」折叠块（运行态 → ✓/✗ + 摘要；重放可见）
- [x] `pytest -q` 全绿（121）；`node --check`；DOM 垫片；冒烟标记

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 8 切片 8.3 条目
- 代码：`agent/tools/subagent_tools.py`、`agent/loop.py`、`agent/web.py`、测试

## 退出决定

- 通过 → 切片 8.4（上下文压缩 compaction）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
