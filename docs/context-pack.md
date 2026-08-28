# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 6 · 完成（Web 界面）**

## 本阶段已完成

- 切片 6.1 极简 Web 终端：标准库 HTTP 服务 + 表单（`python -m agent.web`）
- 切片 6.2 SSE 流式：过程与结果实时推送（EventSource）

## 下一阶段（迭代 7）

- 候选：命令沙箱（真正隔离，替代模式匹配）/ 多 provider 切换
- 开工前先写：SPEC 增项 + CHECKLIST 增项 + 本 context-pack，再动代码

## 不得读 / 不得改

- `.env`（真实凭据）
- 已放行代码（除非必要最小修改）
