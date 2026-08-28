# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 3 · 切片 3.2（自我反思 reflection）**

## 当前阶段目标

模型给出最终答复后注入自检提示：发现问题则继续调用工具修正，确认完成才返回；`--reflect` / `DEEPSEEK_REFLECT` 开启（仅一轮反思，防无限循环）。

## 必须读

- `SPEC.md`（迭代 3 范围）
- `agent/loop.py`（`run_turn` 需加反思轮）
- `agent/config.py`（加 `reflect`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/loop.py`（`REFLECT_PROMPT` + 反思轮）、`agent/config.py`（`reflect`）、`agent/cli.py`（`--reflect`）、`tests/test_loop.py`（+2）
- 验收：`pytest -q` 全绿
