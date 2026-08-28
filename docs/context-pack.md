# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 4 · 切片 4.1（猜你想问）**

## 当前阶段目标

单次任务完成后，再调一次模型生成 2–3 个后续问题建议；`--suggest` 开启，复用同一 client（累计 token）。

## 必须读

- `SPEC.md`（迭代 4 范围）
- `agent/llm.py`（`chat` 无工具调用）
- `agent/parser.py`（`parse_response`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/suggest.py`、`agent/cli.py`（`--suggest`）、`tests/test_suggest.py`
- 验收：`pytest -q` 全绿
