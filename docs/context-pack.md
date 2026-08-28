# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 3 · 切片 3.1（token / 费用统计）**

## 当前阶段目标

`LLMClient` 累计 prompt / completion tokens；单次任务 `--usage`、REPL `/usage` 输出用量与估算费用（DeepSeek 价格常量，标注「估算」）。

## 必须读

- `SPEC.md`（迭代 3 范围）
- `agent/llm.py`（需加累计与 summary）
- `agent/loop.py`（`run` 需支持复用 client）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/llm.py`（usage 累计）、`agent/loop.py`（run 复用 client）、`agent/cli.py`（`--usage`）、`agent/repl.py`（`/usage`）、`tests/test_llm.py`（+1）
- 验收：`pytest -q` 全绿
