# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 8 · 切片 8.6（chat / agent 双模式 + /plan 命令）**

## 当前阶段目标

chat 模式 = 只读工具集（read_file/list_directory/search_content/web_search，不可编辑/执行/委派），agent 模式（默认）= 全部工具；`run(mode=, tools=)` 与 `tool_schemas_for` 参数化；顶栏分段模式切换（localStorage）；`/chat` 按条强制 chat、`/goal` `/plan` 强制 agent；`/plan` = make_plan → `plan` 事件（📐 执行计划块）→ 计划注入执行；`/events` 增 mode/plan 参数。

## 必须读

- `SPEC.md` 第 29 节（本切片范围）
- `agent/loop.py`（`run` 签名与 SYSTEM_PROMPT）、`agent/plan.py`（`make_plan`）、`agent/tools/__init__.py`（`tool_schemas`）、`agent/web.py`（`_handle_events`/`parseCommand`/`sendTask`/顶栏 HTML）
- `tests/test_loop.py`、`tests/test_web.py`、`tests/test_tools.py`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/tools/__init__.py`、`agent/loop.py`、`agent/web.py`、测试
- 验收：`pytest -q` 全绿（约 129）；`node --check`；DOM 垫片（模式切换/命令）；冒烟标记；真实冒烟（chat 只读 + plan 事件）
