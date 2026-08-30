# gate-checklist.md — 迭代 8 · 切片 8.0 放行清单

> 当前阶段：迭代 8 · 切片 8.0（工具扩展 web_search）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `web_search` 工具：默认 DDG lite 无 key（html 端点异常已切换）；SEARCH_API_URL/SEARCH_API_KEY 可插拔；解析标题/URL/摘要；uddg 跳转链接还原
- [x] 注册进工具表（7 工具）与 SYSTEM_PROMPT；错误/超时/空结果/截断行为正确
- [x] 测试覆盖（解析 html/lite 双布局、缺 query、失败、钳制、模板、空结果）；`pytest -q` 全绿（105）；真实外网冒烟成功

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 8 切片 8.0 条目
- 代码：`agent/tools/search_tools.py`、`agent/tools/__init__.py`、`agent/loop.py`、`tests/test_tools.py`

## 退出决定

- 通过 → 切片 8.1（goal 模式）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
