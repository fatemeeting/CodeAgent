# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 8 · 切片 8.5（集成回归，迭代 8 收尾）**

## 当前阶段目标

① AM1 真实任务冒烟：goal 完成路径（`goal=1`，goal_start/goal_end + 产物落盘）、goal 受阻路径（goal_blocked 或非零退出码 + [DONE]）、复合任务（todo + web_search + delegate_subagent 至少触发 todo 与工具结果）、web_search 直连复验；② AM2 全量回归：pytest、compileall、--help、REPL /quit；③ AM3 证据入 AGENT_LOG、CHECKLIST 迭代 8 全勾选放行。

## 必须读

- `CHECKLIST.md` AM 节（8.5 验收项）
- `agent/web.py`（`/events` 参数与事件类型）、`agent/loop.py`（goal/compact/todo/subagent 事件点）

## 不得读 / 不得改

- `.env` 内容（真实凭据；仅应用自身经 `Config.from_env()` 加载）

## 输出要求

- 产出：冒烟脚本（临时）+ 证据记录（AGENT_LOG）
- 验收：pytest 123 全绿；3~4 次真实冒烟断言成立；CLI/REPL 无回归
