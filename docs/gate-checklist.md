# gate-checklist.md — 阶段 4 放行清单

> 当前阶段：阶段 4（上下文管理）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `context.py` 提供 token 估算与历史截断（自研，不引入 tokenizer）
- [x] 截断始终保留 system 与首条 user（任务）
- [x] 超预算时丢弃中间旧消息、保留最近消息
- [x] 孤儿 tool 消息被丢弃（保证 tool calling 配对）
- [x] 主循环接入截断；`--max-context-tokens` 生效
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试输出：见 `docs/AGENT_LOG.md` 阶段 4 条目
- 代码：`agent/context.py`、`agent/config.py`、`agent/loop.py`、`agent/cli.py`、`tests/test_context.py`

## 退出决定

- 通过 → 进入阶段 5（集成回归）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
