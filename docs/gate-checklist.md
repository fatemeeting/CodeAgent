# gate-checklist.md — 迭代 6 v2 · 切片 6.8 放行清单

> 当前阶段：迭代 6 v2 · 切片 6.8（Editor Window + 终端）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] Editor Window 三栏：文件树 | Monaco（CDN，离线回退）| 聊天
- [x] 底部终端：`POST /exec` 复用 `execute_command`，含 dangerous 标记，可折叠
- [x] 模式一键切换且对话状态不丢（消息重放）
- [x] `/tree?deep=1` 递归文件树
- [x] 既有功能不回归；`pytest -q` 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 6 v2 切片 6.8 条目
- 代码：`agent/web.py`、`tests/test_web.py`

## 退出决定

- 通过 → 迭代 6 v2 完成（可做 6.9 主题/持久化，或收尾）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
