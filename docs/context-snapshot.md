# context-snapshot.md — 已完成事实与未决问题

## 已完成事实（截至阶段 3）

- 需求来源已抽取：`requirement_doc/requierment_extracted.txt`
- 关键决策已确认：Python + DeepSeek API + 核心闭环 MVP
- 阶段 0 契约文件齐备；虚拟环境 `.venv` 已建，依赖锁定于 `requirements.lock`
- 阶段 1 骨架冒烟通过；openai 3.x 客户端 API 已验证兼容
- 阶段 2 工具层通过：六个工具 + JSON Schema + 注册表 + dispatch
- CI/CD 就绪：独立 git 仓库 + pre-commit/commit-msg 钩子 + GitHub Actions CI
- 阶段 3 闭环循环通过：parser（分流 + 防御式解析）+ 完整 loop（终止条件 + 错误处理）+ `--workdir`；`pytest` 25 passed；真实端到端「创建 hello.py 并运行」闭环
- 远程仓库已连接并公开：`git@github.com:fatemeeting/CodeAgent.git`（SSH 认证 `fatemeeting`）；main 已推为正确根目录结构（stages 0-3 + CI/CD），旧嵌套历史备份在 `backup/original-nested`
- **CI 已验证通过**：GitHub Actions `CI` conclusion=success（compileall + pytest 25 用例），`.github/workflows/ci.yml` 位于 main 根目录

## 未完成 / 未决

- 上下文管理（阶段 4）：token 预算截断、历史精简策略
- 集成回归（阶段 5）：多任务回归 + 证据
- 提交物（阶段 6）：README.txt（≤1000 字）+ 视频 + 推送到公开仓库

## 下一阶段资料

- 阶段 4（上下文管理）需要：`agent/context.py`、token 估算截断、长对话单测
- 复用：`agent/loop.py` 的消息队列结构、`agent/config.py` 的 `max_iterations`

## 不再重复讨论的决定

- 语言 = Python；模型 = DeepSeek（`deepseek-chat`）；范围 = 核心闭环 MVP
- 仅允许 `openai` 依赖；禁止一切 agent 框架
- `.env` 由 `config.py` 自研解析器加载（不引入 python-dotenv）
- 工具返回字符串观测回填给模型；assistant 消息用 arguments_raw 重建
