# gate-checklist.md — 迭代 6 · 切片 6.3 放行清单

> 当前阶段：迭代 6 · 切片 6.3（工作区先行）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] REPL `/workdir [路径]` 设置 / 查看工作区；提示符显示当前工作区
- [x] Web `/run` `/events` 接受 workdir 参数，不存在则报错
- [x] 未指定时默认行为不变（不回归）
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 6 切片 6.3 条目
- 代码：`agent/repl.py`、`agent/web.py`、`tests/test_repl.py`、`tests/test_web.py`

## 退出决定

- 通过 → 切片 6.4（聊天式界面）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
