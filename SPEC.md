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
```

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

## 13. 迭代 7 · 切片 7.2（前端会话管理 UI + 消息落盘）

范围（仅前端，`agent/web.py` 内嵌页面；后端端点 7.1 已就绪）：

1. **会话栏 UI**：顶栏新增会话下拉（`/sessions` 列表）+ 新建 / 重命名 / 删除按钮；无会话时发送任务自动建会话（名称取任务前 24 字，工作区为当前工作区）。
2. **切换会话**：`GET /sessions/<id>` → 工作区切到会话绑定目录（同步 `ws-name` 与 localStorage、重载文件树），对话区重放会话消息。
3. **消息落盘**：用户消息入列后与 agent 运行结束（`[DONE]`）时，`POST /sessions/<id>/messages` 全量保存 `{role, raw}` 消息列表。

非目标（留给 7.3）：刷新页面后自动恢复最近会话、当前文件恢复、跨标签页同步。

## 14. 迭代 7 · 切片 7.2 体验修复（字体放大 + 会话按钮中文 + 自动命名）

1. **全局字体放大**：页面全部字号上调一档（11→12、12→13、13→14、14→15、标题 26→28），Monaco 编辑器字号 13→14。
2. **会话栏按钮**：新建 / 重命名 / 删除改中文文案并放大（14px、加大内边距），替代 ＋/✎/🗑 图标。
3. **首次会话自动命名**：每个会话第一条用户消息后、运行结束（`[DONE]`）时按首条任务自动重命名（`sessionTitle`：压缩空白、截断 20 字 + 省略号，空任务兜底「新会话」）；新建 / 切换 / 删除会话时清空命名标记。

## 15. 迭代 7 · 切片 7.2 体验修复 2（对话框布局稳定 + 文件手动编辑保存）

1. **对话面板布局稳定**：`#chat-history` 加 `min-height: 0`（长对话时收缩滚动，输入框不再被顶出可视区）；`#chat-inputbar` 加 `flex-shrink: 0`（输入条恒定可见）。
2. **文件手动编辑与保存**：文件头新增「保存」按钮（无文件时隐藏）；Monaco 支持 Ctrl+S；无 Monaco 的回退视图改为可编辑 textarea（行号随滚动/输入同步）；新增后端端点 `POST /save-file`（workdir + path + content，UTF-8 写入，路径越界防护，允许子目录新建文件）。

## 16. 迭代 7 · 切片 7.2 体验修复 3（三栏独立滚动）

1. **三栏各自滚动**：左栏文件树 `#tree-root` 加 `min-height: 0`（修复深层树被裁剪、滚动条不出现的 flex 收缩问题）；中栏 `#editor-host`（Monaco 内置滚动 / 回退 textarea）与右栏 `#chat-history`（min-height: 0 + 输入条 flex-shrink: 0）维持栏内滚动——三栏互不影响，各带自己的滚动条。

## 17. 迭代 7 · 切片 7.2 体验修复 4（Web 恒流式 + 滚动兜底）

1. **Web 恒流式**：`/events` 强制 `stream=True`（`dataclasses.replace` 覆盖配置）——网页无论 `DEEPSEEK_STREAM` 是否开启，最终答复都逐 token 推送；CLI 行为不变。
2. **滚动兜底**：三栏滚动容器加 `overscroll-behavior: contain`（滚轮滚动到边界不再失控）；工作区管理器卡片 `max-height: 92vh + overflow-y: auto`（矮窗口可滚动）；Monaco 创建后 `layout()` + window resize 重排（flex 容器中 automaticLayout 失效兜底）。
3. **消息落盘排队**：`saveMessages` 加 pending 队列——`[DONE]` 落盘不再被进行中的保存跳过。

## 18. 迭代 7 · 切片 7.2 体验修复 5（布局全链路加固 + 缩放自适应）

1. **显式高度链条**：`body` 100vh/100dvh；`#main` height 100vh/100dvh + min-height 0 + overflow hidden；`#content` `height: 0 + flex: 1 + min-height: 0`（铁律模式，内容永不撑高容器）；`.pane` 补 `min-height/min-width: 0`；`#topbar` flex-shrink 0 + overflow hidden——三栏滚动容器在任何窗口尺寸下都获得确定高度。
2. **缩放自适应**：栏宽按视口比例钳制（`clampPanes`：左右栏 ≤ 38vw，resize 时回收并持久化），浏览器缩放/窄窗口下右栏（对话框）不再被推出视口；工作区路径 chip 超长省略号。
3. **防旧页缓存**：`/` 响应加 `Cache-Control: no-store`，刷新即最新页面。

## 19. 迭代 7 · 切片 7.2 体验修复 6（步骤观测乱码）

1. **命令输出编码回退**：`execute_command` 改为字节捕获 + `_decode` 回退链（UTF-8 优先 → 系统本地编码如 CP936/GBK → 容错替换）——Python 子进程输出 UTF-8，cmd 内置命令按控制台代码页输出，按单一 UTF-8 解码会产生乱码。

## 20. 迭代 7 轨迹可视化（切片 7.3–7.6）

> 决策（已与用户确认）：轨迹展示先用**内联折叠块**（Claude Code transcript 风格），「对话 | 轨迹」Tab 全景视图后置迭代 8；think 通过 `.env` 新增 `DEEPSEEK_THINK` 一键切换 `deepseek-reasoner`（显式 `DEEPSEEK_MODEL` 优先）。

1. **架构：类型化事件流替代文本日志**。`loop.py` 增加可选 `emit(event)` 回调（默认 None → CLI/REPL print 路径零回归）；事件类型：`turn_start / think_start / think_delta / think_end / content_delta / round_end{has_tools} / tool_call / tool_result / error / turn_end`；所有事件带 `text` 兜底字段（仅 content_delta 携带正文，旧前端继续流式工作）。
2. **think 捕获**：`llm.py` 流式收集 `delta.reasoning_content`（`on_reasoning` 回调）与非流式挂载 `response.reasoning`（7.3 首项内省 openai 3.x 字段透传，不透传则回退原始解析）；`deepseek-chat` 无该字段时自然降级。
3. **切片 7.3 事件化后端**：上述 emit/回调/`DEEPSEEK_THINK` 配置 + `web.py /events` 发事件帧（stdout 兜底静默，防双通道重复）+ 测试（事件序列 / think / 增量流式 / CLI 回归）。
4. **切片 7.4 前端内联折叠轨迹块**：think 折叠块、tool 折叠行（✓/✗、耗时、展开参数与返回摘要）；`round_end` 边界——工具轮叙述内容折入轨迹、最终答复留在气泡；会话持久化 messages + trace（旧数据兼容）。
5. **切片 7.5 错误处理与状态指示**：error 事件（severity/retryable）、LLM 重试可见化、SSE 断线「连接中断 + 重新连接」、非零退出码/超时染色、回合状态指示（thinking→tool→answering→done）。
6. **切片 7.6 集成回归**：真实任务冒烟（正常 + 错误路径）、CLI/REPL/会话/保存/滚动回归、证据入 AGENT_LOG。
7. **非目标（迭代 8）**：对话/轨迹 Tab 分栏、轨迹导出、跨会话检索、结构化错误驱动的自动恢复闭环。

## 21. 迭代 7 · 切片 7.4-UI（轨迹视觉升级，模仿 DSH DisclosureRow）

> 依据：研读 deepseek-harness 源码（`ReasoningRow` / `GenericCommandCard` / `MessageItem` / `StatsLine` / `design-platform.css`）。仅改 `agent/web.py`，零新依赖。

1. **折叠行一行式**：`图标 标题 · 单行摘要 <meta> ▸`——think 摘要显示思考首行（流式时显示最新行并横向滚动跟随）；tool 摘要显示「工具名 · 参数预览」；整行点击展开。
2. **展开正文分层**：tool/note/err = 代码卡片（margin 4px、padding 12px 16px、1px 浅边框 rgba(0,0,0,.04)、圆角 12px、背景 #f9fafb、等宽 12.5px、max-height 260px 内滚）；think = 标题下缩进 22px 的三级灰文本（无卡片框）。
3. **运行态扫光动画**：running 块头部覆盖 300px 渐变光带 2.6s 循环（纯 CSS，`prefers-reduced-motion` 降级）；状态色：成功 #22c55e / 错误 #ef4444。
4. **气泡与统计行**：用户气泡圆角 22px、padding 10px 16px；回合底部统计行 `N 步 · 工具 Xs · Y tokens`（后端 `turn_end` 事件携带 usage）。
5. **回放兜底**：重放未闭合（缺 think_end / tool_result）的块自动收尾标记。

## 22. 迭代 7 · 切片 7.4-UI2（整体色调与布局细节，模仿 DSH design-platform）

> 两者总布局不同（本项为三栏编辑器 + 聊天），仅借鉴 DSH 的色调系统与组件质感，不改布局结构。

1. **色调切换**：暖白（#f7f7f4/#26251e/橙 #f54e00）→ DSH 冷调（页面 #f5f6f7、面板 #ffffff、近黑 #0f1115、三级灰 #81858c、极浅边框 rgba(0,0,0,.04)、代码底 #f9fafb）；强调色橙 → **DeepSeek 蓝 #4176e6**（hover #2f5fd0、浅底 rgba(65,118,230,.08)）；状态色统一 DSH（绿 #22c55e / 红 #ef4444 / 琥珀 #f59e0b）。
2. **布局细节轻量化**：顶栏/输入区/管理器分隔用 1px 极浅边框；会话按钮改无边框轻按钮（灰字 hover 蓝）；工作区 chip 浅灰底；分隔条改 1px 细线（hover 蓝）；树/最近列表 hover 浅蓝底。
3. **对话质感 DSH 化**：agent 答复改纯文本（去气泡框底，行高 1.65）；输入框白底 16px 圆角 + 聚焦蓝色光晕（0 0 0 3px rgba(65,118,230,.12)）；角色标签 caption 灰。
4. **验证**：pytest 84 无回归；`node --check`；色调/布局标记冒烟；DOM 垫片回归。
