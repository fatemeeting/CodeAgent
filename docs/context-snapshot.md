# context-snapshot.md — 已完成事实与未决问题

## 已完成事实（截至阶段 4）

- 需求来源已抽取：`requirement_doc/requierment_extracted.txt`
- 关键决策已确认：Python + DeepSeek API + 核心闭环 MVP
- 阶段 0 契约文件齐备；虚拟环境 `.venv` 已建，依赖锁定于 `requirements.lock`
- 阶段 1 骨架冒烟通过；openai 3.x 客户端 API 已验证兼容
- 阶段 2 工具层通过：六个工具 + JSON Schema + 注册表 + dispatch
- CI/CD 就绪：独立 git 仓库 + pre-commit/commit-msg 钩子 + GitHub Actions CI
- 阶段 3 闭环循环通过：parser + 完整 loop + `--workdir`；真实端到端「创建 hello.py 并运行」闭环
- 远程仓库已连接并公开：`git@github.com:fatemeeting/CodeAgent.git`；GitHub Actions `CI` conclusion=success
- 阶段 4 上下文管理通过：自研 token 估算 + 历史截断（保留 system+任务+最近、丢弃孤儿 tool）；`--max-context-tokens` 生效；`pytest` 32 passed

## 未完成 / 未决

- 集成回归（阶段 5）：多任务回归 + 证据
- 提交物（阶段 6）：README.txt（≤1000 字）+ 视频 + 推送到公开仓库

## 下一阶段资料

- 阶段 5（集成回归）需要：2–3 个真实任务回归、核对旧功能不回退、证据入 AGENT_LOG
- 复用：`python -m agent "<任务>" --workdir <目录>` 端到端流程

## 不再重复讨论的决定

- 语言 = Python；模型 = DeepSeek（`deepseek-chat`）；范围 = 核心闭环 MVP
- 仅允许 `openai` 依赖；禁止一切 agent 框架
- `.env` 由 `config.py` 自研解析器加载（不引入 python-dotenv）
- 工具返回字符串观测回填给模型；assistant 消息用 arguments_raw 重建
- token 估算是启发式（ASCII≈4 字符/token、CJK≈1 字符/token），非精确 tokenizer
