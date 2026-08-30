# gate-checklist.md — 迭代 8 · 切片 8.6 放行清单

> 当前阶段：迭代 8 · 切片 8.6（chat/agent 双模式 + /plan）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] chat 模式只读工具集 + system prompt 约束；agent 全工具；`run(mode=, tools=)` / `tool_schemas_for`
- [x] 顶栏模式切换（localStorage 持久化）；`/chat`、`/goal`、`/plan` 命令按条强制对应模式
- [x] `/plan`：plan 事件 + 计划注入执行；`/events` mode/plan 参数
- [x] `pytest -q` 全绿（127）；`node --check`；DOM 垫片；冒烟标记；真实冒烟（chat 只读 + plan 执行）

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 8 切片 8.6 条目
- 代码：`agent/tools/__init__.py`、`agent/loop.py`、`agent/web.py`、测试

## 退出决定

- 通过 → 迭代 8 正式收尾（用户决定）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
