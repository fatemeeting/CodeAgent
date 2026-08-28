# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 2 · 完成（多轮 REPL + 会话持久化）**

## 本阶段已完成

- 切片 2.1 多轮 REPL：无参进入交互模式，跨轮保留历史，命令 `/help` `/quit` `/clear` `/history`
- 切片 2.2 会话持久化：`/save [路径]` `/load [路径]`，`context.py` 的 `save_history` / `load_history`

## 下一阶段（迭代 3）

- 候选：自我反思（reflection）/ token 费用统计 / 流式输出 / 「猜你想问」
- 开工前先写：SPEC 增项 + CHECKLIST 增项 + 本 context-pack，再动代码

## 不得读 / 不得改

- `.env`（真实凭据）
- 已放行代码（除非必要最小修改）
