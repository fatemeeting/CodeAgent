# 编程智能体（Coding Agent）

## 仓库地址
https://github.com/fatemeeting/CodeAgent

## 项目简介
从零实现的 Python 命令行编程智能体。用户给出编程任务，agent 通过 DeepSeek 大模型自主读写文件、执行命令、列目录、搜索内容，循环调用本地工具直至完成任务，类似简化的 Claude Code / OpenCode。未使用任何 agent 框架，核心逻辑（对话历史与上下文管理、工具定义与本地执行、模型输出解析、循环终止条件、错误处理）全部自研。

## 如何运行
1. 环境要求：Python ≥ 3.10
2. 安装依赖：pip install -r requirements.txt
3. 配置凭据：复制 .env.example 为 .env，填入 DEEPSEEK_API_KEY（凭据绝不入库）
4. 单次任务：python -m agent "你的编程任务" [--workdir 目录] [--max-iterations N]
5. 交互模式：python -m agent（无任务参数；支持 /save /load 持久化、/usage 查看用量）

示例：
python -m agent "创建 hello.py 打印 Hello 并运行"

## 特色功能
- 六个本地工具：read_file / write_file / edit_file / execute_command / list_directory / search_content
- 交互式多轮会话（REPL）+ 会话持久化（跨进程恢复）
- 自我反思（--reflect）：最终答复前自检，发现问题自动修正
- 原生 function calling（OpenAI 兼容接口），仅依赖 openai 客户端库
- 自研 token 估算与上下文截断，长任务不爆上下文
- token / 费用统计（--usage）
- 流式输出（--stream）：最终答复逐 token 输出
- 「猜你想问」（--suggest）：任务完成后推荐后续问题
- 过程可读：实时打印每步工具调用与结果
- 49 个单元测试（mock LLM 免 key）+ GitHub Actions CI + pre-commit 密钥扫描

## 其它说明
- 凭据一律通过环境变量或 .env 提供，绝不入库
- 完整开发过程见 git 提交历史与 docs/AGENT_LOG.md
