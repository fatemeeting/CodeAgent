# context-snapshot.md — 已完成事实与未决问题

## 已完成事实（截至阶段 5）

- 需求来源已抽取：`requirement_doc/requierment_extracted.txt`
- 关键决策已确认：Python + DeepSeek API + 核心闭环 MVP
- 阶段 0 契约文件齐备；虚拟环境 `.venv` 已建（Python 3.11.9），依赖锁定于 `requirements.lock`
- 阶段 1 骨架冒烟通过；openai 3.x 客户端 API 已验证兼容
- 阶段 2 工具层通过：六个工具 + JSON Schema + 注册表 + dispatch
- CI/CD 就绪：独立 git 仓库 + pre-commit/commit-msg 钩子 + GitHub Actions CI
- 阶段 3 闭环循环通过：parser + 完整 loop + `--workdir`；真实端到端「创建 hello.py 并运行」闭环
- 远程仓库已连接并公开：`git@github.com:fatemeeting/CodeAgent.git`；GitHub Actions `CI` conclusion=success
- 阶段 4 上下文管理通过：自研 token 估算 + 历史截断；`pytest` 32 passed
- 阶段 5 集成回归通过：3 个真实任务（写+执行 / 改+验证 / 列+搜索）全部闭环，32 测试无回退
- CHECKLIST：A/B/C/E/F 全部通过，D 仅剩 D1（过程可读）一项

## 未完成 / 未决

- D1（体验）：主循环暂不打印每步工具调用过程（loop 静默执行，仅返回最终答案）——视频演示前建议补上
- 提交物（阶段 6）：README.txt（≤1000 字）+ 视频 + 推送 stage 4/5 到远程

## 下一阶段资料

- 阶段 6（提交物）需要：README.txt、2 分钟演示视频脚本、推送
- 若补 D1：在 `agent/loop.py` 每步打印「工具名 + 参数 + 观测摘要」

## 不再重复讨论的决定

- 语言 = Python；模型 = DeepSeek（`deepseek-chat`）；范围 = 核心闭环 MVP
- 仅允许 `openai` 依赖；禁止一切 agent 框架
- `.env` 由 `config.py` 自研解析器加载（不引入 python-dotenv）
- 工具返回字符串观测回填给模型；assistant 消息用 arguments_raw 重建
- token 估算是启发式（ASCII≈4 字符/token、CJK≈1 字符/token），非精确 tokenizer
