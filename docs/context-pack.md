# context-pack.md — 当前阶段上下文包

> 当前阶段：**阶段 3（闭环循环）**

## 当前阶段目标

实现完整主循环：解析模型输出（文本 / tool_calls 分流）、执行工具并回填结果、循环终止条件（无工具调用 / 最大迭代上限）、错误处理（工具异常回填）；CLI 接入 `--workdir`。用 mock 单测验证循环逻辑，再用真实任务端到端冒烟。

## 必须读

- `SPEC.md`（范围：闭环循环、终止条件、错误处理）
- `CHECKLIST.md`（A9–A12、B1、D1 项）
- `AGENTS.md`（禁止事项与安全边界）
- `agent/tools/__init__.py`（`tool_schemas()` / `dispatch()` 接口）
- `docs/context-snapshot.md`（阶段 2 已完成事实）

## 可读（按需）

- `agent/llm.py`（`chat` 接口与重试）
- `agent/config.py`（`Config` 字段）

## 不得读 / 不得改

- `.env`（真实凭据）
- 已放行阶段的代码（除非必要最小修改）

## 输出要求

- 产出：`agent/parser.py`、完整 `agent/loop.py`、`agent/cli.py`（加 `--workdir`）、`tests/test_parser.py`、`tests/test_loop.py`
- 验收：`pytest -q` 免 key 全绿；真实任务「创建 hello.py 并运行」闭环
