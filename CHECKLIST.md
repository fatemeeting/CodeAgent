# CHECKLIST.md — 验收清单

> 每一项都必须「可观察或可执行」验证。通过 = 有命令输出 / 文件 / 日志等证据，并记入 `docs/AGENT_LOG.md`。
> 状态：`[ ]` 未验 / `[x]` 已验。

## A. 功能

- [x] A1 `python -m agent --help` 正常显示用法并以 0 退出
- [x] A2 给定「你好」能返回模型文本回复（阶段 1 冒烟）
- [x] A3 `read_file` 能读取指定文件内容并返回给模型
- [x] A4 `write_file` 能创建 / 覆盖文件
- [x] A5 `edit_file` 能对匹配串做最小替换且不改无关内容
- [x] A6 `execute_command` 能执行命令并捕获 stdout / stderr / 退出码
- [x] A7 `list_directory` 能列出目录条目
- [x] A8 `search_content` 能按关键字 / 正则返回命中行
- [x] A9 模型返回一次 `tool_call` 后能自动执行、回填并再次调用模型
- [x] A10 模型返回纯文本（无工具调用）时循环正确终止
- [x] A11 达到 `--max-iterations` 上限时终止并给出说明
- [x] A12 端到端真实任务「创建 hello.py 并运行输出」能闭环完成

## B. 工程

- [x] B1 `python -m pytest -q` 全程免 key 通过（mock LLM）
- [x] B2 `python -m compileall agent` 无语法错误
- [x] B3 `requirements.txt` 仅含 `openai`（不出现任何 agent 框架）
- [x] B4 源码无 `import langchain / llama_index / autogen / crewai` 等被禁依赖
- [x] B5 提交信息包含阶段名；提交历史完整、未改写

## C. 安全

- [x] C1 仓库不含真实 `DEEPSEEK_API_KEY`（`git grep` 扫描通过）
- [x] C2 `.env` 被 `.gitignore` 忽略（`git status --ignored` 可见且未被跟踪）
- [x] C3 `execute_command` 有超时，失败不回退为无限重试
- [x] C4 无 `rm -rf`、`git push --force`、生产环境操作等危险路径

## D. 体验

- [x] D1 主循环过程可读：展示每步工具调用与结果摘要
- [x] D2 空状态（无历史 / 无工具）不报错
- [x] D3 终端中文输出正常、不溢出

## E. 解释（答辩可辩护）

- [x] E1 能说清五要素（Spec / Context / Tools / Checks / Exit）各自对应代码位置
- [x] E2 能说清为何用原生 function calling 而非框架
- [x] E3 能说清终止条件与死循环防护
- [x] E4 能说清上下文截断策略及其代价

## F. 退出条件（Gate）

- [x] F1 阶段 0 契约文件齐备且被人工审阅
- [x] F2 A1–A12 与 B、C 全部通过，D / E 至少各通过 2 项
- [x] F3 每个失败项都定位到具体切片，且只修该切片
- [x] F4 `docs/AGENT_LOG.md` 记录了每阶段证据与放行决定

## G. 迭代 2（多轮会话 + 持久化）

- [x] G1 无任务参数启动进入 REPL；`/quit` `/clear` `/history` `/help` 生效
- [x] G2 多轮对话跨轮保留历史（第 2 轮理解「刚才」）
- [x] G3 `/save` `/load` 持久化会话，跨进程恢复
- [x] G4 单次任务模式 `python -m agent "任务"` 不回归

## H. 迭代 3（token 统计 + 自我反思）

- [x] H1 `--usage` / `/usage` 输出 token 用量与估算费用
- [x] H2 `--reflect` 注入自检，发现问题则修正，确认完成返回原答复
- [x] H3 未开启 reflect 时行为不变（不回归）

## I. 迭代 4（猜你想问 + 流式输出）

- [x] I1 `--suggest` 任务完成后推荐后续问题
- [x] I2 `--stream` 最终答复流式输出，不重复打印
- [x] I3 未开启 stream / suggest 时行为不变（不回归）

## J. 迭代 5（任务规划 + 并行工具 + 人工确认）

- [x] J1 `--plan` 执行前输出分步计划并注入执行上下文
- [x] J2 多个 tool_calls 并发执行，观测按序回填
- [x] J3 `--confirm` 危险命令确认：拒绝不执行、确认执行
- [x] J4 未开启时行为不变（不回归）

## K. 迭代 6（Web 界面）

- [x] K1 `python -m agent.web` 标准库 HTTP 服务（零新依赖）
- [x] K2 表单提交任务，显示过程与结果
- [x] K3 SSE 流式实时推送（[DONE] 结束）
- [x] K4 CLI 功能不受影响（不回归）

## L. 迭代 6 优化（工作区先行 + 聊天式界面）

- [x] L1 REPL `/workdir` 设置工作区，提示符显示当前工作区
- [x] L2 Web `/run` `/events` 接受 workdir 参数并校验
- [x] L3 聊天式 Web 界面：气泡 + 流式 + 工具着色（模仿 DSH）
- [x] L4 既有功能不回归

## M. 迭代 6 优化（原生文件夹选择器）

- [x] M1 前端「📂 选择」→ 服务端 tkinter 唤起系统文件夹对话框
- [x] M2 所选路径填入工作区输入框；无图形环境优雅降级

## N. 迭代 6 v2（Cursor 风格重写 · 切片 6.6）

- [x] N1 未选工作区只显示整页工作区管理器
- [x] N2 管理器三要素：选择 / 确认（显式 + `/tree` 校验）/ 管理（最近列表 + 🔄 切换）
- [x] N3 `GET /tree` 目录条目与不存在报错
- [x] N4 暖白视觉系统（#f7f7f4 / #26251e / #f54e00、8px 间距）

## O. 迭代 6 v2（Agent Window · 切片 6.7）

- [x] O1 左栏对话：气泡 + SSE 流式 + 工具着色 + Enter 发送
- [x] O2 右栏文件页：右上文件名 tab + 下拉切换 + 行号视图
- [x] O3 任务完成后自动展示最新修改文件
- [x] O4 `GET /file` 内容 / 不存在 / 越界防护

## P. 迭代 6 v2（Editor Window · 切片 6.8）

- [x] P1 Editor 三栏：文件树 | Monaco（CDN，离线回退）| 聊天
- [x] P2 底部终端：`/exec` 复用 execute_command + dangerous 标记 + 可折叠
- [x] P3 模式一键切换且对话状态不丢（消息重放）
- [x] P4 `/tree?deep=1` 递归文件树

## Q. 迭代 6 v2 修复（Markdown 渲染 + 代码纯净）

- [x] Q1 对话窗口渲染 Markdown（代码块/行内代码/粗体/标题/列表，零依赖）
- [x] Q2 SYSTEM_PROMPT 禁止把 Markdown 标记写进代码文件
