# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 5 · 切片 5.2（并行工具调用）**

## 当前阶段目标

模型一次返回多个 tool_calls 时并发执行（API 契约：同批工具相互独立），观测仍按调用顺序回填；单工具不变。

## 必须读

- `SPEC.md`（迭代 5 范围）
- `agent/loop.py`（`run_turn` 工具执行段）
- `agent/tools/__init__.py`（`dispatch`）

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/loop.py`（ThreadPoolExecutor 并行 + 日志顺序）、`tests/test_loop.py`（+1）
- 验收：`pytest -q` 全绿
