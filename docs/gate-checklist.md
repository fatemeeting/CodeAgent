# gate-checklist.md — 迭代 8 · 切片 8.1 放行清单

> 当前阶段：迭代 8 · 切片 8.1（goal 模式）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] goal 语义：非「完成」开头自动续跑（注入续跑提示）；「受阻：」→ blocked；连续 3 轮无进展 → blocked；goal 与 reflect 互斥
- [x] 事件 goal_start/progress/blocked/end{status}；goal 状态持久化（update_goal）；恢复 open 会话注入中断上下文
- [x] 前端受阻 warn 块 + 状态指示；CLI `--goal`、`.env.example` 同步
- [x] `pytest -q` 全绿（111）；DOM 垫片；CLI 回归（compileall/--help）

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 8 切片 8.1 条目
- 代码：`agent/loop.py`、`agent/config.py`、`agent/cli.py`、`agent/sessions.py`、`agent/web.py`

## 退出决定

- 通过 → 切片 8.2（todo 任务清单）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
