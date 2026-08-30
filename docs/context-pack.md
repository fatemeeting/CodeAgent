# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 8 · 切片 8.0（工具扩展 web_search）**

## 当前阶段目标

新增 `web_search` 工具：标准库 `urllib` + `html.parser`（零新依赖）；默认 DuckDuckGo HTML 接口（无 key），`SEARCH_API_URL`（`{query}` 模板）/`SEARCH_API_KEY` 可插拔；返回 `[N] 标题 / URL / 摘要`（200 字截断、15s 超时、失败回填错误观测）；注册进工具表并更新 SYSTEM_PROMPT。

## 必须读

- `SPEC.md` 第 27 节（迭代 8 计划）
- `agent/tools/base.py`、`agent/tools/__init__.py`（注册方式）、`agent/tools/shell_tools.py`（`_decode` 编码回退参考）
- `agent/loop.py`（SYSTEM_PROMPT）、`tests/test_tools.py`

## 不得读 / 不得改

- `.env`（真实凭据；SEARCH_API_KEY 由工具运行时经 os.environ 读取，不落盘）

## 输出要求

- 产出：`agent/tools/search_tools.py`、`agent/tools/__init__.py`、`agent/loop.py`、`tests/test_tools.py`
- 验收：`pytest -q` 全绿（约 104）；外网冒烟一次（受限则 mock 证据 + 如实记录）
