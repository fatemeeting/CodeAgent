# SPEC.md — 编程智能体（Coding Agent）

> 依据：`requirement_doc/推免考核题目学生版.pdf`（软件工程专业推免项目，已抽取文本至 `requirement_doc/requierment_extracted.txt`）。
> 本文档回答「做什么」；「怎么验收」见 `CHECKLIST.md`；「运行边界」见 `AGENTS.md`。

## 1. 用户与目标

- **用户**：个人独立开发者（软件工程推免项目作者，需向评委讲解并辩护设计决策）。
- **目标**：用 Python 从零实现一个 CLI 编程智能体。用户给出编程任务后，agent 通过与 DeepSeek 大模型交互，**自主**读写文件、执行命令，循环调用本地工具，直至完成该编程任务。
- **成功判定**：给定一个真实编程任务（例如「创建 hello.py 并运行输出」），agent 无需人工干预即可闭环完成，且过程与结果可观察、可复现。

## 2. 范围（Scope，本期 = 核心闭环 MVP）

1. 单轮任务驱动、多轮工具循环的主循环（loop）。
2. 六个本地工具：
   - `read_file`（读文件）
   - `write_file`（写 / 覆盖文件）
   - `edit_file`（按匹配串做最小替换）
   - `execute_command`（在指定工作目录执行 shell 命令，带超时）
   - `list_directory`（列目录）
   - `search_content`（按关键字 / 正则搜索文件内容）
3. 自研核心逻辑（对应题目「重要逻辑需自行编写」清单）：
   - 对话历史与上下文管理（system prompt、消息队列、token 预算截断）
   - 工具定义（JSON Schema）与本地执行（subprocess / 文件 IO）
   - 模型输出解析（文本与 `tool_calls` 分流，防御式解析）
   - 循环终止条件（无工具调用 / 最大迭代上限 / 显式停止）
   - 错误处理（工具异常回填为观测、API 失败重试）
4. CLI 入口与参数（任务文本、`--model`、`--max-iterations`、`--workdir`）。

## 3. 非目标（Non-goals，本期明确不做）

- 会话持久化（跨进程恢复历史）
- 多模型 / 多 provider 切换
- 任务规划器、多子 agent、并发编排
- 流式输出（SSE）
- GUI / Web 界面（仅命令行）
- 远程 / 沙箱代码执行（命令在本机工作目录内执行）
- 自动安装依赖、Git 提交等危险自动化

## 4. 技术约束

- **语言**：Python ≥ 3.10。
- **模型**：DeepSeek（OpenAI 兼容接口，`base_url=https://api.deepseek.com`，模型 `deepseek-chat`），通过原生 function calling 调用工具。
- **依赖**：仅 `openai` 官方客户端库；**禁止**任何 agent 框架 / SDK（LangChain、LlamaIndex、OpenAI Agents SDK、Claude Agent SDK、AutoGen、CrewAI 等）。
- **禁止**依赖 API 服务端托管的代码执行或文件工具（Code Interpreter、Files API）。
- **凭据**：`DEEPSEEK_API_KEY` 等一律走环境变量或 `.env`（未入库），绝不写入仓库、README.txt 或视频。
- **执行边界**：`execute_command` 默认限制在 `--workdir`（默认当前目录）内，必须带超时。

## 5. 阶段划分（8 阶段小合同）

| # | 阶段 | 交付物 / 验收 | Exit 条件 |
|---|------|--------------|-----------|
| 0 | 契约先行 | SPEC / CHECKLIST / AGENTS / 工程基础文件 | 契约齐备，人工放行 |
| 1 | 骨架冒烟 | 包结构 + `config.py` + `llm.py` + 最小 loop（无工具） | 能启动、能访问 API、无基础错误 |
| 2 | 工具层 | 六个工具 + schema + 注册表 + 单测 | 每个工具独立可测、可回退 |
| 3 | 闭环循环 | `parser.py` + 完整 `loop.py` + 终止条件 + 错误处理 | 一次任务完整闭环 |
| 4 | 上下文管理 | `context.py` token 预算截断 + 单测 | 长对话不爆上下文 |
| 5 | 集成回归 | 2–3 个真实任务 + 证据入 `docs/AGENT_LOG.md` | 失败定位到具体切片 |
| 6 | 提交物 | `README.txt` + 视频脚本 + 历史整理 | 三项提交物齐备 |

## 6. 目录结构

```
coding-agent/
├── README.txt            # 提交物（阶段 6）
├── requirements.txt      # 仅 openai
├── .gitignore / .env.example
├── SPEC.md / CHECKLIST.md / AGENTS.md
├── agent/                # 源码（阶段 1 起）
├── tests/                # 单元测试（mock LLM，免 key）
└── docs/                 # 契约工作文件 + prompts/

## 7. 迭代 2（增量：多轮会话 + 持久化）

在 MVP 基础上增量：

1. **交互式多轮会话（REPL）**：无任务参数启动进入交互模式，连续输入任务，agent 跨轮保留对话历史（复用 token 截断）。命令：`/help` `/quit` `/clear` `/history`。
2. **会话持久化**：REPL `/save [路径]` / `/load [路径]` 命令（`context.py` 的 `save_history` / `load_history`），消息历史序列化为 JSON，跨进程恢复。

迭代 2 仍不做：流式输出、多 provider、任务规划、Web UI、命令沙箱。

## 8. 迭代 3（增量：token 统计 + 自我反思）

1. **token / 费用统计**：`LLMClient` 累计 prompt / completion tokens；`--usage` 或 REPL `/usage` 输出用量与估算费用（价格常量标注估算）。
2. **自我反思（reflection）**：模型给出最终答复后注入自检提示，发现问题则继续调用工具修正，确认完成才返回（`--reflect` 开启）。

## 9. 迭代 4（增量：猜你想问 + 流式输出）

1. **「猜你想问」**：单次任务完成后，再调一次模型生成 2–3 个后续问题建议（`--suggest` 开启）。
2. **流式输出**：最终答复逐 token 输出（`--stream` 开启），工具调用轮仍走非流式。

## 10. 迭代 5（增量：任务规划 + 并行工具 + 人工确认）

1. **任务规划（plan-first）**：`--plan` 执行前先输出分步计划，再把计划注入执行上下文。
2. **并行工具调用**：模型一次返回多个 tool_calls 时并发执行（独立工具）。
3. **human-in-the-loop**：`--confirm` 危险命令（rm / del / git push 等）执行前请求人工确认。

## 11. 迭代 6（增量：Web 界面）

1. **极简 Web 终端**：自写标准库 HTTP 服务（`http.server`，零新依赖），表单提交任务、显示过程与结果。
2. **SSE 流式**：过程日志与最终答复通过 Server-Sent Events 实时推送到浏览器。
3. **工作区先行**：REPL `/workdir <路径>` 设置工作区（提示符显示当前工作区）；Web 表单先填工作区再提交任务，服务端校验目录存在。
4. **聊天式 Web 界面**：模仿 DeepSeek Harness 的对话式布局（消息气泡 + 流式过程 + 工作区选择）。
5. **原生文件夹选择器**：Web 端「📂 选择」按钮 → 服务端用 tkinter（标准库）唤起系统文件夹选择对话框，返回路径填入工作区。
6. **Cursor 风格重写（v2）**：暖白视觉系统（`#f7f7f4` / `#26251e` / `#f54e00`、8px 间距）；**工作区管理器**（选择 / 确认 / 管理三要素 + 最近列表 + 目录校验，未选工作区不显示其它内容）；**Editor Window 布局**（左文件树 | 中 Monaco 代码编辑（CDN，文件名 tab 按需显示）| 右 AI 聊天，三栏宽度可拖拽）；代码编辑器走 CDN Monaco（B 策略，前端运行时资源，不进入 Python 依赖）。

## 12. 迭代 7（持久化管理：Session + 工作区 + 对话记录）

1. **服务端会话存储（决策：JSON 文件）**：`agent/sessions.py` 的 `SessionStore`——`data/sessions/<id>.json` 单文件一会话 + `index.json` 索引，线程安全（RLock）；会话绑定工作区。
2. **Session CRUD 端点**：`GET/POST /sessions`、`GET/DELETE /sessions/<id>`、`POST /sessions/<id>/messages`（全量保存消息）。
3. **前端会话管理与恢复**（切片 7.2/7.3）：会话列表 / 新建 / 切换 / 重命名 / 删除；刷新后恢复最近会话（消息重放 + 工作区 + 当前文件）。
```
