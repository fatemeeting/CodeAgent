# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 5 · 切片 5.1（任务规划 plan-first）**

## 当前阶段目标

执行前先让模型输出分步计划（3–6 步），打印后把计划注入执行上下文；`--plan` 开启。

## 必须读

- `SPEC.md`（迭代 5 范围）
- `agent/suggest.py`（同款「复用 client 再调一次」模式）
- `agent/parser.py`（`parse_response`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/plan.py`、`agent/cli.py`（`--plan`）、`tests/test_plan.py`
- 验收：`pytest -q` 全绿；`--plan` 真实冒烟
