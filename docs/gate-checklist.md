# gate-checklist.md — 迭代 6 · 切片 6.5 放行清单

> 当前阶段：迭代 6 · 切片 6.5（原生文件夹选择器）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `pick_workspace` 用 tkinter 唤起系统对话框，失败优雅返回 None
- [x] `POST /pick-workspace` 返回所选路径（或错误提示）
- [x] 前端「📂 选择」按钮填入工作区输入框
- [x] 既有功能不回归；`pytest -q` 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 6 切片 6.5 条目
- 代码：`agent/web.py`、`tests/test_web.py`

## 退出决定

- 通过 → 迭代 6 优化完成
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
