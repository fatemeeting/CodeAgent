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

## 23. 迭代 7 · 切片 7.5（错误处理与状态指示）

1. **LLM 重试可见化**：`chat`/`chat_stream` 增加 `on_retry(attempt, max, exc)` 回调，loop 事件化为 `retry` 事件；前端琥珀色 `↻ 重试 n/m · 原因` 行（DSH retry-shimmer 风格简化版）。
2. **错误分级**：error 事件带 `severity`/`retryable`；工具参数 JSON 解析失败**不执行**、事件化（severity=error、retryable=true）并回填错误观测供模型修正。
3. **非零退出码染色**：`tool_result` 事件携带 `exit_code`（execute_command 观测解析）；前端 `⚠ exit N` 琥珀色（0 绿 ✓ / 非零琥珀 ⚠ / 工具错误红 ✗）。
4. **SSE 断线**：`es.onerror` 关闭流（防重复运行）并渲染「连接中断，请重新发送任务」错误行（服务端单次任务不支持断点续传，如实提示重发）。
5. **回合状态指示**：Agent 标签旁状态点（思考中… / 调用工具… / 回答中… / 完成·绿 / 出错·红），脉冲动画 + reduced-motion 降级。

## 24. 迭代 7 · 切片 7.5 修复（同会话上下文互通）

1. **根因**：`/events` 每次 `run()` 均从 `[system, user(task)]` 全新开始，会话历史未传给模型（CLI REPL 有历史，Web 没有）。
2. **修复（参考 DSH 多轮设计）**：`run()` 增可选 `history`（前置对话消息）；`/events` 接受 `session` 参数 → 从 `SessionStore` 加载该会话消息 → `_history_from_session` 转换（跳过空占位、剔除与当前任务相同的最后一条用户消息防重复）→ 注入本轮；前端 EventSource URL 携带当前会话 id；无 session 参数时行为不变（旧调用兼容）。
3. **审计顺带确认**：消息保存有 pending 队列（保存与读取竞态安全：先存后读剔除当前任务，未存则 run 自增，均不重复）；`truncate_history` 对注入历史同样生效（token 预算保护）。

## 25. 迭代 7 · 切片 7.5 修复 2（会话归属工作区）

> 参考 Cursor / Claude Code / OpenHands 的工作区级会话隔离：会话列表只显示当前工作区的会话。

1. **后端**：`SessionStore.list_sessions(workspace=None)` 增工作区过滤（`_normalize_ws`：反斜杠→正斜杠、去尾分隔符、Windows 忽略大小写）；`GET /sessions?workspace=<路径>` 透传；无参数返回全部（旧调用兼容）。
2. **前端**：`loadSessions(ws)` 带 `workspace` 参数拉取；当前会话不属于该工作区时自动置空（下拉回「（新会话）」）；切换工作区（管理器确认）时重置当前会话引用与对话；切换会话 / 新建 / 重命名 / 删除均按当前工作区刷新下拉；新建会话仍绑定当前工作区。

## 26. 迭代 7 · 切片 7.5 修复 3（DSH 对齐：工作区物理分层 + 中断轮次标记）

> 依据 DSH `session-persistence-jsonl` 磁盘布局（`<root>/<normalized-cwd>/<encoded-id>/session.jsonl`）做低成本的等价简化。

1. **存储物理分层**：`data/sessions/<ws-slug>/<id>.json`（slug = 归一化工作区安全目录名 + 8 位 md5 防碰撞）；根 `index.json` 不变（仍带 workspace 字段）；旧版平铺 `<id>.json` 在 `SessionStore` 初始化时自动迁移到工作区目录（迁移失败保留旧文件，读取走兼容路径）；`_session_path` 优先识别旧平铺文件（兼容），否则按 index 中的 workspace 定位。
2. **中断轮次标记**：切换/重放会话时，若最后一条 agent 消息的 trace 无 `turn_end` → 前端追加 `turn_end {interrupted: true}` 事件，轨迹渲染琥珀「上次中断 · 上次运行在此中断，未完成」行（对齐 DSH 的 interrupted closer 语义）；error 事件 severity=warn 渲染为琥珀 warn 行（error 红 / warn 琥珀分级）。
3. **不做**（超需求）：zstd 压缩、SQLite 后端、write-behind 批次、fsync 持久性保证。

## 27. 迭代 8（生命周期与编排的 DSH 对齐）

> 对齐 DSH 的 goal / todo / subagent / compaction 能力 + web_search 工具扩展。全程走既有事件流架构（emit 回调 + 前端折叠块），CLI 零回归，仅 openai 依赖不变。

1. **切片 8.0 工具扩展 web_search**：标准库 `urllib` + `html.parser`（零新依赖）；默认 DuckDuckGo HTML 接口（无需 key），`SEARCH_API_URL`（`{query}` 模板）与 `SEARCH_API_KEY` 可插拔自定义 API；`web_search {query, max_results(1-10,默认5)}` → `[N] 标题 / URL / 摘要`（摘要 200 字截断）；15s 超时、失败回填错误观测（复用 tool_result 染色，无新事件）；只读 GET 安全。
2. **切片 8.1 goal 模式**：长目标自动续跑（显式 DONE 信号 + 提高迭代预算）、连续 N 轮无进展 → `blocked` 事件终止；goal 状态（open/blocked/done + 摘要）持久化到会话；恢复会话注入中断上下文（简化 `TOOL_OUTCOME_UNKNOWN`：提示先验证副作用、只重试幂等操作）；事件 `goal_start/goal_progress/goal_blocked/goal_end`；Web 目标徽章。
3. **切片 8.2 todo 任务清单**：`todo_write` 工具（`{id, content, status}` 清单）+ `todo` 事件（全量快照）+ 前端清单折叠块与进度条；随 trace 持久化重放可见。
4. **切片 8.3 subagent 工具**：`delegate_subagent {task}`（子线程独立 run、短预算、不可再委托，摘要回填）；并行由既有工具并行执行天然获得（不做 workflow DSL）；事件 `subagent_start/subagent_end`；前端嵌套轨迹块。
5. **切片 8.4 上下文压缩**：历史超 `max_context_tokens` 时先 LLM 总结旧轮次为摘要（system 后插入）再按预算保留最近消息（替代直接丢弃）；`compact` 事件（压缩前后 token 数）；前端「上下文压缩」折叠块；仅 Web 会话历史启用；压缩失败回退旧截断逻辑。
6. **切片 8.5 集成回归**：真实冒烟 ×3~4（goal 完成/受阻、复合 todo+subagent、web_search）；全量回归；证据入 AGENT_LOG 放行。
7. **降级路径**：goal 无进展检测降级为轮数上限；subagent 预算 3 轮失败不重试；compaction 阈值 ≥80% 预算才触发。

## 29. 迭代 8 · 切片 8.6（chat / agent 双模式 + /plan 命令）

1. **双模式**：chat 模式 = 只读工具集（read_file/list_directory/search_content/web_search），不可编辑文件、执行命令、委派子代理；agent 模式（默认）= 全部 9 工具；模式约束写入 system prompt。
2. **模式切换**：顶栏分段控件（💬 Chat / 🤖 Agent，localStorage 持久化）；`/chat <消息>` 按条强制 chat；`/goal`、`/plan` 按条强制 agent。
3. **/plan 命令**：agent 模式下先 `make_plan` 生成计划 → `plan` 事件（前端 📐 执行计划块）→ 计划注入任务后执行（对齐 CLI `--plan`）。
4. **后端**：`/events` 增 `mode`（chat/agent，默认 agent）与 `plan`（1 开启）参数；`run(mode, tools)` 参数化；`tool_schemas_for(names)` 工具集选择。
5. **输入栏模式按钮**：输入框左侧胶囊按钮（🤖 Agent / 💬 Chat）点击切换并 localStorage 持久化（顶栏切换移除）。
6. **斜杠命令浮层**：输入 `/` 弹出 `/goal`、`/plan` 选择浮层（图标 + 描述、前缀过滤、悬停/选中高亮、↑↓/Enter/Esc 键盘导航、点击插入）。

## 30. 迭代 9（Skills 模块）

> 参考 Claude Code 的 `SKILL.md` 与 DSH `packages/skill`；技能即文件，实时加载生效。

1. **技能模型**：技能 = 目录 + `SKILL.md`（轻量 frontmatter：name/description/keywords/modes + 指南正文，零新依赖；正文限 4000 字）。
2. **三级目录（就近覆盖，按 name 去重）**：内置 `skills/`（只读，随发行）< `SKILLS_DIR` 外部目录（只读，跨项目共享）< 工作区 `<workdir>/.codeagent/skills/`（可写，用户增删改，文件树可见）。
3. **生命周期（增删改 = 文件操作）**：新增 = 表单（POST /skills）或直建目录；删除 = 浮层 🗑（DELETE /skills/<name>，仅工作区级可删、越界防护）或删目录；改动 = Monaco 编辑保存（复用 /save-file）或表单（PUT /skills/<name>）；每次 run 实时加载，改完即生效。
4. **使用（仅显式指定，无自动匹配）**：技能装载必须由用户显式指定——`/skill` 命令：输入 `/skill` 后同一命令浮层列出全部技能，点击累积多选（逗号分隔，可多次点选/再点取消），随后可跟任务文本；技能管理浮层（浏览/✎编辑/🗑删除/只读标签）由顶栏「📚 技能」入口打开；CLI `--skill NAME`（可重复）；任务文本不做自动关键词匹配（`match_skills` 保留为后续「推荐技能」预留，不接入 run）。**命令可组合**：`/skill` 是独立维度，可与 `/goal`、`/plan`、`/chat` 组合（如 `/goal <任务> /skill a,b` 或 `/skill a,b /goal <任务>`）；`/goal` 与 `/plan` 互斥——同时出现只生效先出现的一个。
5. **切片**：9.1 存储与解析（已完成）；9.2 注入与命令（显式指定注入 + skill_loaded 事件 + CLI）；9.3 事件与技能管理 UI（skill_loaded 块 + /skills CRUD 端点与浮层）；9.4 内置技能（python-testing / code-review / web-frontend）；9.5 集成回归。

## 31. 迭代 10（/plan 两段式人工确认）

> 用户需求：/plan 模式下模型先告知用户具体计划，询问是否修改，**等待用户确认后**才继续执行。

1. **Web `/plan <任务>`（两段式）**：
   - 第一段（生成）：`/events?plan=1` 只调规划器生成计划，发 `plan` 事件（`status: pending`，带 `task`/`skill` 供恢复），随后 `content_delta`「已生成执行计划，请确认、修改或取消。」并**结束本回合（不执行工具循环）**；前端在计划块下渲染确认栏：✓ 确认执行 / ✎ 修改计划 / ✕ 取消。
   - 确认：前端以 `plan_text=<计划>` 再发 `/events` → 服务端发 `plan` 事件（`status: confirmed`）并把「已确认的执行计划：…请严格按计划逐步执行。」注入任务后正常执行。
   - 修改：前端带 `plan=1&plan_feedback=<意见>` 再发 → 规划器带用户意见重新生成，再次 `pending` 暂停，直至确认或取消。
   - 取消：不发起任何执行；确认栏收起，标注「已取消」。
   - 重放/刷新恢复：pending 计划事件携带 task/skill，重放轨迹后确认栏可重新出现（仅最后一个 plan 事件为 pending 时）。
2. **CLI `--plan`（交互确认）**：打印计划后询问「是否按此计划执行？(y=执行 / n=取消 / 输入修改意见重新生成)」；输入意见 → 带意见重新生成并再次询问；非交互（EOF/管道）视为取消并退出。
3. **降级**：计划生成失败 → `error{severity: warn}` 提示后按无计划直接执行（不卡住用户）。
4. **不变**：`/plan` 与 `/goal` 互斥（取先出现者）；与 `/skill` 可组合；chat 模式不生效（/plan 强制 agent）。

## 28. 迭代 8 · 切片 8.1 补充（/goal 斜杠命令）

1. **对话输入命令**：输入 `/goal <任务>` 时本回合进入目标模式（任务文本去掉前缀，EventSource 带 `goal=1`）；仅输入 `/goal` 时占位符闪烁用法提示；`/plan`、`/chat` 命令后续切片实现。
2. **后端**：`/events` 解析 `goal` 查询参数 → `dataclasses.replace(config, stream=True, goal=True)` 按次生效；goal 状态持久化仅在 goal 模式或恢复 open 会话时写入（避免普通对话覆盖已完成的 goal 状态）。
