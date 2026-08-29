# gate-checklist.md — 迭代 7 · 切片 7.1 放行清单

> 当前阶段：迭代 7 · 切片 7.1（Session 后端）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `SessionStore`：创建 / 列表（按 updated_at 倒序）/ 读取 / 重命名 / 删除 / 全量存消息，线程安全
- [x] `/sessions` 端点：GET 列表 / POST 新建 / GET 详情 / POST 消息 / DELETE 删除，非法 id 报错
- [x] `data/` 加入 `.gitignore`（会话数据不入库）
- [x] `pytest -q` 全绿（72 passed）；真实服务冒烟通过

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 7 切片 7.1 条目
- 代码：`agent/sessions.py`、`agent/web.py`、`tests/test_sessions.py`、`tests/test_web.py`

## 退出决定

- 通过 → 切片 7.2（前端会话管理 UI + 消息落盘）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
