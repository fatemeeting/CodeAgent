# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 8 · 切片 8.4（上下文压缩 compaction）**

## 当前阶段目标

`loop.py` 新增 `_maybe_compact(client, config, messages, emit)`：仅 Web（emit 非空）且历史 ≥ 80% `max_context_tokens` 且消息 > 8 条时——把「system 之后、最近 6 条之前」的 user/assistant 旧轮次交给 LLM 压缩为 ≤300 字摘要，替换为 `[上下文压缩摘要] …` assistant 消息；发 `compact {before, after, summary}` 事件；压缩失败回退旧截断逻辑；随后照常 `truncate_history`。CLI（emit None）不启用（零回归）。前端渲染「📦 上下文压缩」折叠块（`before → after tokens` meta + 摘要正文）。

## 必须读

- `SPEC.md` 第 27 节切片 8.4
- `agent/loop.py`（`run_turn` 每轮开头的 truncate 调用点）、`agent/context.py`（`estimate_tokens`/`_message_text`）、`agent/web.py`（`handleEvent`）
- `tests/test_loop.py`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/loop.py`、`agent/web.py`、`tests/test_loop.py`
- 验收：`pytest -q` 全绿（约 124）；`node --check`；DOM 垫片（压缩块）；冒烟标记；CLI 回归（emit None 不触发）
