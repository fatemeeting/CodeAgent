# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 10 · 切片 10.1（/plan 两段式人工确认）**

## 当前阶段目标

把 `/plan` 从「出计划后立即执行」改为**两段式**：先生成计划展示并暂停（`plan{status:pending}`，不执行工具循环），前端确认栏 ✓确认执行 / ✎修改计划 / ✕取消；确认后携带 `plan_text` 注入「已确认的执行计划」再执行（`plan{status:confirmed}`）；修改则带 `plan_feedback` 重新生成再次暂停；取消不执行。CLI `--plan` 同步改为交互确认（y/n/修改意见），非交互视为取消。计划生成失败降级直接执行。`/plan` 与 `/goal` 互斥、与 `/skill` 组合不变。

## 必须读

- `SPEC.md` 第 31 节、`CHECKLIST.md` AW 节
- `agent/plan.py`（make_plan）、`agent/web.py`（`_handle_events` worker plan 分支、`handleEvent` plan 块、`sendTask`/`newTurnState`/`renderTraceFromEvents`）、`agent/cli.py`（--plan）
- `tests/test_plan.py`、`tests/test_web.py`（`test_web_sse_chat_mode_readonly_and_plan`）

## 不得读 / 不得改

- `.env`（真实凭据）
- `agent/loop.py`/`agent/llm.py`（无需改）

## 输出要求

- 产出：`agent/plan.py`、`agent/web.py`、`agent/cli.py`、`tests/test_plan.py`、`tests/test_web.py`
- 验收：`pytest -q` 全绿（约 152）；`node --check` + 无头垫片（确认/修改/取消/重放）；真实冒烟（plan=1 暂停 → plan_text 执行；CLI 交互确认）
