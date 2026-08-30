# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 8 · 切片 8.1（goal 模式：长目标续跑 + 受阻检测 + 状态持久化 + 恢复注入）**

## 当前阶段目标

goal 模式（`DEEPSEEK_GOAL=1` / CLI `--goal` / Web 目标模式）：模型无工具回复若不以「完成」开头 → 注入续跑提示自动继续；以「受阻：原因」开头 → blocked；连续 3 轮续跑无进展 → blocked；事件 `goal_start / goal_progress / goal_blocked / goal_end{status}`；goal 状态（status + 摘要）持久化到会话（`SessionStore.update_goal`）；恢复 open 状态会话时注入中断上下文（先验证副作用、只重试幂等操作）；前端受阻 warn 块 + 状态指示。goal 与 reflect 互斥（goal 优先）。

## 必须读

- `SPEC.md` 第 27 节切片 8.1
- `agent/loop.py`（`run`/`run_turn` 无工具分支与事件点）、`agent/config.py`、`agent/cli.py`（flag 注册）
- `agent/sessions.py`（CRUD 与 `_write_session`）、`agent/web.py`（`_handle_events` worker 与 `handleEvent`）
- `tests/test_loop.py`、`tests/test_sessions.py`、`tests/test_web.py`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/loop.py`、`agent/config.py`、`agent/cli.py`、`agent/sessions.py`、`agent/web.py`、`.env.example`、测试
- 验收：`pytest -q` 全绿（约 112）；DOM 垫片（blocked 块/状态）；CLI `--goal` 回归；真实 goal 冒烟（可选）
