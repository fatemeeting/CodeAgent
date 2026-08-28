# context-snapshot.md — 已完成事实与未决问题

## 已完成事实（截至阶段 1）

- 需求来源已抽取：`requirement_doc/requierment_extracted.txt`
- 关键决策已确认：Python + DeepSeek API + 核心闭环 MVP
- 阶段 0 契约文件齐备（SPEC / CHECKLIST / AGENTS / 工程基础文件 / docs 工作文件）
- 虚拟环境 `.venv`（Python 3.11.9）已建，依赖锁定于 `requirements.lock`（openai 3.3.1 / pytest 9.1.1）
- 阶段 1 骨架冒烟通过：`--help` 正常；`python -m agent "你好"` 返回真实模型回复
- openai 3.x 客户端 API 已验证兼容（`OpenAI(api_key, base_url)` + `chat.completions.create(..., tools=...)`）

## 未完成 / 未决

- 工具层（阶段 2）：六个工具 + JSON Schema + 注册表 + 单测
- 闭环循环（阶段 3）：parser / 终止条件 / 错误处理
- 上下文管理（阶段 4）：token 预算截断

## 下一阶段资料

- 阶段 2（工具层）需要：`agent/tools/` 包、六个工具的 JSON Schema 与本地执行、mock 单测

## 不再重复讨论的决定

- 语言 = Python；模型 = DeepSeek（`deepseek-chat`）；范围 = 核心闭环 MVP
- 仅允许 `openai` 依赖；禁止一切 agent 框架
- `.env` 由 `config.py` 自研解析器加载（不引入 python-dotenv）
