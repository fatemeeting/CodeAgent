# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 7 · 切片 7.6（集成回归，迭代 7 收尾）**

## 当前阶段目标

① AG1 真实任务冒烟 ×2（正常路径：创建+运行文件闭环；错误路径：不存在的命令 → 非零退出码/失败信号），经真实 `/events` 事件流端到端验证（需工作区 `.env` 的真实 key，经应用自身加载，不读取/打印凭据）；② AG2 旧功能回归：pytest 全量、`compileall`、`--help`、REPL `/quit`（无 LLM 调用）、Web 端点测试；③ AG3 证据入 AGENT_LOG、CHECKLIST 迭代 7 全勾选放行。

## 必须读

- `CHECKLIST.md` AG 节（7.6 验收项）
- `agent/web.py`（`/events` 事件流与事件类型）、`agent/loop.py`（事件产生点）

## 不得读 / 不得改

- `.env` 内容（真实凭据；仅允许应用自身经 `Config.from_env()` 加载）

## 输出要求

- 产出：冒烟脚本（临时）+ 证据记录（AGENT_LOG）
- 验收：pytest 98 全绿；两次真实冒烟均以 `[DONE]` 收尾且断言成立；CLI/REPL 无回归
