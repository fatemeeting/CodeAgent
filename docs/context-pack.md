# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 7 · 切片 7.3（事件化后端 + think 捕获 + 模型切换）**

## 当前阶段目标

`loop.py` 增加可选 `emit(event)` 回调（默认 None → CLI print 零回归），产出类型化事件（turn_start/think_*/content_delta/round_end/tool_call/tool_result/error/turn_end，均带 `text` 兜底字段）；`llm.py` 捕获 `reasoning_content`（流式 `on_reasoning`/`on_content` 回调 + 非流式挂载 `response.reasoning`）；`config.py` 增 `DEEPSEEK_THINK` 开关（切 deepseek-reasoner，显式 DEEPSEEK_MODEL 优先）；`web.py /events` 发事件帧（stdout 兜底静默）。

## 必须读

- `SPEC.md` 第 20 节（迭代 7 轨迹可视化完整计划）
- `agent/llm.py`（`chat`/`chat_stream`/`_chat_stream_once`/`_build_streamed_response`）
- `agent/loop.py`（`run`/`run_turn`/`_log_tool_call`/`_execute_tool_calls`）
- `agent/config.py`、`agent/web.py`（`_handle_events` worker 与写循环）
- `tests/test_llm.py`、`tests/test_loop.py`、`tests/test_config.py`、`tests/test_web.py`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/llm.py`、`agent/loop.py`、`agent/config.py`、`agent/web.py`、`.env.example`、对应测试
- 验收：`pytest -q` 全绿（约 82）；`/events` 事件帧冒烟；openai 3.x `reasoning_content` 字段透传内省
