# context-pack.md — 当前阶段上下文包

> 当前阶段：**阶段 4（上下文管理）**

## 当前阶段目标

实现对话历史管理与 token 预算截断：自研 token 估算（不引入 tokenizer）、截断时保留 system + 首条 user（任务）+ 最近消息、丢弃孤儿 tool 消息；接入主循环与 `--max-context-tokens`。

## 必须读

- `SPEC.md`（范围：上下文管理、token 截断）
- `CHECKLIST.md`（B1 项；长对话不爆上下文）
- `agent/loop.py`（消息队列结构）
- `docs/context-snapshot.md`（阶段 3 已完成事实）

## 可读（按需）

- `agent/config.py`（Config 字段）
- `agent/parser.py`（消息重建格式）

## 不得读 / 不得改

- `.env`（真实凭据）
- 已放行阶段的代码（除非必要最小修改）

## 输出要求

- 产出：`agent/context.py`、`agent/config.py`（加 `max_context_tokens`）、`agent/loop.py`（接入截断）、`agent/cli.py`（加 `--max-context-tokens`）、`tests/test_context.py`
- 验收：`pytest -q` 免 key 全绿
