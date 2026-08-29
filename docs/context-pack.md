# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 6 v2 · 切片 6.7（Agent Window：对话 + 文件页）**

## 当前阶段目标

Agent Window 左栏：对话历史（气泡、SSE 流式、工具调用着色）+ 底部输入框（Enter 发送）；右栏：文件页（**右上方文件名 tab** + 文件切换下拉 + 行号代码视图）；任务完成后自动展示最新修改文件。后端新增 `GET /file`（含路径越界防护）。B 策略的 Monaco 留待 6.8 编辑器模式。

## 必须读

- `SPEC.md`（迭代 6 增补 6）
- `agent/web.py`（`INDEX_HTML` / `do_GET` / `_workspace_tree`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/web.py`（`GET /file` + `_handle_file` + 前端对话/文件页）、`tests/test_web.py`（+1）
- 验收：`pytest -q` 全绿；冒烟（file 端点 + 页面标记）
