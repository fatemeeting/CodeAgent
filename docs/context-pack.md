# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 7 · 切片 7.2（前端会话管理 UI + 消息落盘）**

## 当前阶段目标

`agent/web.py` 内嵌页面新增会话栏（列表 / 新建 / 切换 / 重命名 / 删除）；无会话时发送任务自动建会话；切换会话 = 切工作区 + 消息重放；用户消息入列与 `[DONE]` 时全量保存消息到服务端。后端 `/sessions` 端点（7.1）已就绪，本切片不动后端。

## 必须读

- `SPEC.md` 第 13 节（切片 7.2 范围与非目标）
- `agent/web.py`（内嵌 HTML/JS：`buildChat` / `sendTask` / SSE `[DONE]` / `enterMain` / 顶栏结构）
- `agent/sessions.py`（端点返回结构：`{ok, session/sessions}`、`get_session` 含 `messages`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）
- 后端 `agent/sessions.py` 与 `/sessions` 端点逻辑（7.1 已放行，只读）

## 输出要求

- 产出：`agent/web.py`（会话栏 HTML/CSS/JS + 落盘钩子）
- 验收：`pytest -q` 全绿（72）；提取内嵌 JS 过 `node --check`；真实服务冒烟（页面标记 + `/sessions` CRUD 往返）
