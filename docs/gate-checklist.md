# gate-checklist.md — 迭代 8 · 切片 8.2 放行清单

> 当前阶段：迭代 8 · 切片 8.2（todo 任务清单）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `todo_write` 工具：全量覆盖、status 校验、≤30 项、内容截断、确认回复计数；注册进工具表（8 工具）
- [x] loop 在 todo_write 成功后发 `todo` 事件（快照）；SYSTEM_PROMPT 提及
- [x] 前端「📋 任务清单」块（状态行 + 完成/总数 meta；原位更新不重复；重放可见）
- [x] `pytest -q` 全绿（117）；`node --check`；DOM 垫片；冒烟标记

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 8 切片 8.2 条目
- 代码：`agent/tools/todo_tools.py`、`agent/loop.py`、`agent/web.py`、测试

## 退出决定

- 通过 → 切片 8.3（subagent 工具）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
