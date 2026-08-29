# gate-checklist.md — 迭代 6 v2 · 切片 6.7 放行清单

> 当前阶段：迭代 6 v2 · 切片 6.7（Agent Window）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 左栏对话：气泡 + SSE 流式 + 工具着色 + Enter 发送
- [x] 右栏文件页：右上文件名 tab + 下拉切换 + 行号视图
- [x] 任务完成后自动展示最新修改文件
- [x] `GET /file` 内容 / 不存在报错 / 越界防护
- [x] 既有功能不回归；`pytest -q` 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 6 v2 切片 6.7 条目
- 代码：`agent/web.py`、`tests/test_web.py`

## 退出决定

- 通过 → 切片 6.8（Editor Window + 终端 + Monaco）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
