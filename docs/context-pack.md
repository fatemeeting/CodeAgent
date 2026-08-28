# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 2 · 切片 2.1（多轮 REPL）**

## 当前阶段目标

实现交互式多轮会话：无任务参数启动进入 REPL，连续输入任务，跨轮保留对话历史（复用 token 截断与 D1 过程打印）。命令 `/help` `/quit` `/clear` `/history`。单次任务模式 `python -m agent "任务"` 不回归。

## 必须读

- `SPEC.md`（迭代 2 范围）
- `agent/loop.py`（`run` 主循环，需重构出 `run_turn`）
- `agent/context.py`（`truncate_history`）
- `docs/context-snapshot.md`

## 可读（按需）

- `agent/cli.py`（入口）

## 不得读 / 不得改

- `.env`（真实凭据）
- 已放行代码（除非必要最小重构）

## 输出要求

- 产出：`agent/repl.py`、重构 `agent/loop.py`（`run_turn`）、`agent/cli.py`（无参→REPL）、`tests/test_repl.py`
- 验收：`pytest -q` 全绿；多轮真实冒烟跨轮记住上下文
