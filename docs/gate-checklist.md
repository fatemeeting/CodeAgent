# gate-checklist.md — 迭代 7 · 切片 7.2 放行清单

> 当前阶段：迭代 7 · 切片 7.2（前端会话管理 UI + 消息落盘）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 顶栏会话栏：下拉（`/sessions` 列表）+ 新建 / 重命名 / 删除；无会话时发送任务自动建会话（名取任务前 24 字、工作区为当前工作区）
- [x] 切换会话：`GET /sessions/<id>` → 工作区切换（ws-name / localStorage / 重载文件树）+ 消息重放
- [x] 消息落盘：用户消息入列后与 `[DONE]` 时 `POST /sessions/<id>/messages` 全量保存
- [x] `pytest -q` 全绿（72）；内嵌 JS 过 `node --check`；真实服务冒烟（页面标记 + CRUD 往返）

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 7 切片 7.2 条目
- 代码：`agent/web.py`（会话栏 + `ensureSession` / `saveMessages` 等）

## 退出决定

- 通过 → 切片 7.3（刷新后恢复最近会话：消息重放 + 工作区 + 当前文件）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
