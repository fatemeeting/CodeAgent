# context-snapshot.md — 已完成事实与未决问题

## 已完成事实（截至阶段 2）

- 需求来源已抽取：`requirement_doc/requierment_extracted.txt`
- 关键决策已确认：Python + DeepSeek API + 核心闭环 MVP
- 阶段 0 契约文件齐备；虚拟环境 `.venv` 已建，依赖锁定于 `requirements.lock`
- 阶段 1 骨架冒烟通过：`--help` 正常；`python -m agent "你好"` 返回真实模型回复
- openai 3.x 客户端 API 已验证兼容
- 阶段 2 工具层通过：六个工具 + JSON Schema + 注册表 + dispatch；`pytest -q` 10 passed
- execute_command 的 subprocess 管道捕获在沙箱正常（EPERM 风险排除）
- CI/CD 就绪：独立 git 仓库（分支 main）+ pre-commit/commit-msg 钩子 + GitHub Actions CI；`pytest` 已扩至 17 用例

## 未完成 / 未决

- 闭环循环（阶段 3）：parser（text/tool_calls 分流）、工具执行→回填→再调模型、终止条件、错误处理
- 上下文管理（阶段 4）：token 预算截断
- CLI 尚未接入 `--workdir`（阶段 3 补齐）

## 下一阶段资料

- 阶段 3（闭环循环）需要：`agent/parser.py`、完整 `agent/loop.py`（接入 tools + 终止条件）
- 参考 `agent/tools/__init__.py` 的 `tool_schemas()` 与 `dispatch()`

## 不再重复讨论的决定

- 语言 = Python；模型 = DeepSeek（`deepseek-chat`）；范围 = 核心闭环 MVP
- 仅允许 `openai` 依赖；禁止一切 agent 框架
- `.env` 由 `config.py` 自研解析器加载（不引入 python-dotenv）
- 工具返回字符串观测回填给模型（stage 3 沿用此约定）
