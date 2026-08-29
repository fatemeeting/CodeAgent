# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 7 · 切片 7.1（Session 后端：模型 + CRUD 端点）**

## 当前阶段目标

服务端会话存储：`agent/sessions.py` 的 `SessionStore`（JSON 文件 + 索引、线程安全）；`agent/web.py` 增 `/sessions` 系列端点；`data/` 入 `.gitignore`。前端 UI 与恢复在 7.2/7.3。

## 必须读

- `SPEC.md`（迭代 7 范围）
- `agent/web.py`（`do_GET` / `do_POST` 路由结构与 `serve`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/sessions.py`、`agent/web.py`（端点 + `server.sessions`）、`tests/test_sessions.py`、`tests/test_web.py`（+session 端点）、`.gitignore`（+`data/`）
- 验收：`pytest -q` 全绿；冒烟（建会话/存消息/删除）
