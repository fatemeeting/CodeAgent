# gate-checklist.md — 迭代 2 · 切片 2.2 放行清单

> 当前阶段：迭代 2 · 切片 2.2（会话持久化）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `save_history` / `load_history` 序列化消息历史（JSON，不含凭据）
- [x] REPL `/save [路径]` `/load [路径]` 生效
- [x] 跨进程恢复历史（加载后能回忆之前内容）
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 2 切片 2.2 条目
- 代码：`agent/context.py`、`agent/repl.py`、`tests/test_context.py`、`tests/test_repl.py`

## 退出决定

- 通过 → 迭代 2 完成（可进迭代 3）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
