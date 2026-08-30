# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 7 · 切片 7.5（错误处理与状态指示）**

## 当前阶段目标

① LLM 重试可见化：`llm.py` 的 `chat`/`chat_stream` 增 `on_retry` 回调，`loop.py` 事件化 `retry` 事件，前端琥珀 `↻ 重试 n/m · 原因` 行；② 错误分级：error 事件带 severity/retryable，工具参数 JSON 解析失败不执行并事件化 + 回填错误观测；③ `tool_result` 携带 `exit_code`（execute_command 观测正则提取），前端 0 绿 / 非零琥珀 ⚠ / 错误红 ✗；④ SSE 断线：关闭流 + 「连接中断，请重新发送任务」错误行（单次任务不支持断点续传，如实降级）；⑤ Agent 标签旁回合状态指示（思考/工具/回答/完成/出错 + 脉冲动画）。

## 必须读

- `SPEC.md` 第 23 节（本切片范围）
- `agent/llm.py`（重试循环）、`agent/loop.py`（tool 执行段与事件点）、`agent/parser.py`（`_parse_arguments` 的 `_error` 占位）、`agent/web.py`（`handleEvent`/`appendAgentMsg`/`sendTask` 的 `es.onerror`）

## 不得读 / 不得改

- `.env`（真实凭据）
- `agent/sessions.py` 与 CRUD 端点（只读）

## 输出要求

- 产出：`agent/llm.py`、`agent/loop.py`、`agent/web.py`、`tests/test_llm.py`、`tests/test_loop.py`
- 验收：`pytest -q` 全绿（约 88）；`node --check`；DOM 垫片（retry 行/exit 染色/断线行/状态指示）；冒烟标记
