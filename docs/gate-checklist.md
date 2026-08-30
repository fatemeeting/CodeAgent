# gate-checklist.md — 迭代 7 · 切片 7.5 放行清单

> 当前阶段：迭代 7 · 切片 7.5（错误处理与状态指示）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `on_retry` 回调 → `retry` 事件 → 前端 `↻ 重试 n/m · 原因` 行
- [x] error 事件 severity/retryable；参数 JSON 解析失败不执行 + 事件化 + 回填观测
- [x] `tool_result.exit_code`（execute_command 观测提取）；前端 0 绿 / 非零琥珀 ⚠ / 错误红 ✗
- [x] SSE 断线：关闭流 + 「连接中断，请重新发送任务」行（去重）
- [x] 回合状态指示（思考中…/调用工具…/回答中…/完成/出错）
- [x] `pytest -q` 全绿（88）；`node --check`；DOM 垫片；冒烟标记

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 7 切片 7.5 条目
- 代码：`agent/llm.py`、`agent/loop.py`、`agent/web.py`、测试

## 退出决定

- 通过 → 切片 7.6（集成回归）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
