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
- [x] P2 `POST /exec` 命令端点（复用 execute_command + dangerous 标记；终端 UI 后按用户要求移除，端点保留）
- [x] P3 模式一键切换且对话状态不丢（消息重放）
- [x] P4 `/tree?deep=1` 递归文件树

## Q. 迭代 6 v2 修复（Markdown 渲染 + 代码纯净）

- [x] Q1 对话窗口渲染 Markdown（代码块/行内代码/粗体/标题/列表，零依赖）
- [x] Q2 SYSTEM_PROMPT 禁止把 Markdown 标记写进代码文件

## R. 迭代 6 v2 布局精简

- [x] R1 删除 Agent Window 与模式切换（仅 Editor Window）
- [x] R2 文件头删除下拉框；文件名 tab 未点文件时隐藏

## S. 迭代 6 v2 交互修复（栏宽拖拽 + 文件树点击）

- [x] S1 三栏宽度可拖拽调整（分隔条 + localStorage 持久化）
- [x] S2 点击文件树文件在中央代码栏显示（Monaco 竞态修复 + CDN 兜底）

## T. 迭代 6 v2 稳定性修复（中/右栏显示）

- [x] T1 逐栏 try/catch 隔离：任一栏构建失败不影响其它栏
- [x] T2 Monaco 加载防御：async 加载、双 CDN 兜底、8 秒超时回退行号视图

## U. 迭代 6 v2 精简与美化（终端移除 + 聊天框）

- [x] U1 终端面板模块完全移除（HTML/CSS/JS 无残留）
- [x] U2 聊天框美化：胶囊圆角发送按钮 + 角色标签（你/Agent）+ 消息置顶 + 空状态提示

## V. 迭代 7 切片 7.1 会话后端（JSON 存储 + CRUD 端点）

- [x] V1 `agent/sessions.py` `SessionStore`：`data/sessions/<id>.json` + `index.json`，线程安全（RLock），名称净化与 id 去重
- [x] V2 REST 端点：GET `/sessions`、GET `/sessions/<id>`、POST `/sessions`、POST `/sessions/<id>`（重命名）、POST `/sessions/<id>/messages`、DELETE `/sessions/<id>`，统一 `{ok, ...}` 响应
- [x] V3 `data/` 加入 `.gitignore`；测试覆盖（`test_sessions.py` 6 项 + `test_web_sessions` 1 项），72 passed + 真实服务冒烟通过

## W. 迭代 7 切片 7.2 前端会话管理 UI + 消息落盘

- [x] W1 顶栏会话栏：下拉列表（`/sessions`）+ 新建 / 重命名 / 删除按钮；无会话时发送任务自动建会话
- [x] W2 切换会话：工作区切到会话绑定目录（同步 ws-name / localStorage / 重载文件树），对话区重放会话消息
- [x] W3 消息落盘：用户消息入列后与 `[DONE]` 时 `POST /sessions/<id>/messages` 全量保存 `{role, raw}`

## X. 迭代 7 切片 7.2 体验修复（字体放大 + 会话按钮中文 + 自动命名）

- [x] X1 全局字体放大：CSS 字号整体上调一档（11→12、12→13、13→14、14→15、标题 26→28），Monaco 13→14
- [x] X2 会话栏按钮：新建 / 重命名 / 删除改中文文案并放大（14px + 加大内边距）
- [x] X3 首次会话自动命名：首条用户消息运行结束后按任务自动重命名（截断 20 字 + …，空任务兜底）

## Y. 迭代 7 切片 7.2 体验修复 2（对话框布局稳定 + 文件编辑保存）

- [x] Y1 对话面板稳定：`#chat-history` min-height:0、`#chat-inputbar` flex-shrink:0，长对话输入框不消失
- [x] Y2 文件头「保存」按钮 + Monaco Ctrl+S + 回退 textarea 可编辑（行号同步）
- [x] Y3 `POST /save-file` 端点：UTF-8 写入、越界防护、子目录新建；测试覆盖

## Z. 迭代 7 切片 7.2 体验修复 3（三栏独立滚动）

- [x] Z1 左栏 `#tree-root` 加 `min-height: 0`：深层文件树出现滚动条而非被裁剪
- [x] Z2 三栏滚动互不影响：左（树）/ 中（Monaco 或回退 textarea）/ 右（聊天）各带滚动条，输入条恒定可见

## AA. 迭代 7 切片 7.2 体验修复 4（Web 恒流式 + 滚动兜底）

- [x] AA1 `/events` 强制 stream=True：网页无论配置如何都逐 token 流式输出（CLI 不变）
- [x] AA2 滚动兜底：三栏滚动容器 `overscroll-behavior: contain`；管理器卡片 max-height 92vh 可滚动；Monaco layout()/resize 重排
- [x] AA3 `saveMessages` 排队去重：`[DONE]` 落盘不被进行中的保存跳过

## AB. 迭代 7 切片 7.2 体验修复 5（布局全链路加固 + 缩放自适应）

- [x] AB1 显式高度链：`#main` height 100vh/100dvh、`#content` height:0+flex:1、`.pane` min-height/min-width:0、`#topbar` flex-shrink:0
- [x] AB2 缩放自适应：`clampPanes` 栏宽 ≤ 38vw（resize 回收 + 持久化）；工作区 chip 超长省略
- [x] AB3 `/` 响应 `Cache-Control: no-store` 防旧页缓存

## AC. 迭代 7 切片 7.2 体验修复 6（步骤观测乱码）

- [x] AC1 `execute_command` 字节捕获 + `_decode` 编码回退链（UTF-8 → 本地编码 → GBK → 容错）
- [x] AC2 测试覆盖：UTF-8 / GBK 回退 / 显式列表 / 全失败容错；真实命令冒烟

## AD. 迭代 7 切片 7.3 事件化后端（轨迹可视化基础）

- [x] AD1 `loop.py` emit 回调：turn_start/think_*/content_delta/round_end/tool_call/tool_result/error/turn_end 事件（emit=None 时 CLI print 零回归）
- [x] AD2 `llm.py` 捕获 reasoning_content（流式 on_reasoning/on_content 回调 + 非流式挂载 response.reasoning）
- [x] AD3 `config.py` `DEEPSEEK_THINK` 开关：开启切 deepseek-reasoner（显式 DEEPSEEK_MODEL 优先）；`.env.example` 同步
- [x] AD4 `web.py /events` 事件帧（type+text，旧前端兼容）；测试更新（事件序列/think/增量流式）

## AE. 迭代 7 切片 7.4 前端内联折叠轨迹块 + 结构化持久化

- [x] AE1 think 折叠块 + tool_call/tool_result 折叠行（✓/✗、耗时、展开参数与返回）
- [x] AE2 round_end 边界：工具轮叙述内容折入轨迹、最终答复留在气泡
- [x] AE3 会话持久化 messages + trace；旧数据兼容
- [x] AE4 折叠展开修复：`style.display = 'block'`（空串回落 CSS display:none 导致展开为空的 bug）
- [x] AE5 文案优化：叙事块 →「Model Assistant」、工具块 →「Tools」（工具名/参数/返回在展开内容）
- [x] AE6 Tools 展开改原始格式：`tool: name` / `parameter: <原始 arguments JSON>` / `output: <观测>`（后端改发 `arguments_raw`；旧会话 args 字段兼容）
- [x] AE7 轨迹不截断：`parameter` 全文原始 JSON；`output` 完整多行观测（模型上下文仍按 MAX_TOOL_TEXT 截断，互不影响）
- [x] AE8 折叠行一行式：图标+标题+单行摘要+箭头（think 摘要=首行/流式最新行，tool 摘要=工具名+参数预览）
- [x] AE9 展开正文卡片化（12px 圆角/浅边框/#f9fafb/等宽/260px 内滚）+ think 缩进文本 + 运行态扫光 + reduced-motion 降级 + 气泡 22px
- [x] AE10 回合统计行（步数/工具耗时/tokens，turn_end 带 usage）+ 回放未闭合块兜底
- [x] AE11 色调切换：冷调 bluish 中性 + DeepSeek 蓝 #4176e6（页面 #f5f6f7 / 近黑 #0f1115 / 三级灰 #81858c / 极浅边框 rgba(0,0,0,.04) / 代码底 #f9fafb / 状态色 #22c55e #ef4444）
- [x] AE12 布局轻量化：极浅分隔、无边框轻按钮、1px 细分隔条（hover 蓝）、agent 答复纯文本化、输入框白底 16px 圆角 + 蓝色聚焦光晕

## AF. 迭代 7 切片 7.5 错误处理与状态指示

- [x] AF1 error 事件（severity/retryable）与 LLM 重试可见化
- [x] AF2 SSE 断线「连接中断 + 重新发送任务」（关闭流防重复运行；单次任务无断点续传，如实降级）
- [x] AF3 非零退出码/超时染色；参数解析失败事件化；回合状态指示
- [x] AF4 SSE 正常结束误报修复：`t.done` 标记（EOF onerror 不再误报断线）+ 事件序列化防御（TypeError 降级为错误帧）
- [x] AF5 同会话上下文互通：`run(history=)` + `/events?session=` 加载会话历史注入本轮（跳过空占位/剔除当前任务防重复）；超长历史按 max_context_tokens 截断；无 session 参数不回归
- [x] AF6 会话归属工作区：`list_sessions(workspace=)` 归一化过滤 + `GET /sessions?workspace=`；前端下拉只显示当前工作区会话，切换工作区重置会话引用
- [x] AF7 存储物理分层：`data/sessions/<ws-slug>/<id>.json`（slug + md5 防碰撞，id 全局唯一检查）；旧平铺文件初始化自动迁移；兼容读取
- [x] AF8 中断轮次标记：重放无 turn_end 的末轮追加 `turn_end{interrupted}` → 琥珀「上次中断」行；error severity=warn 琥珀分级

## AG. 迭代 7 切片 7.6 集成回归

- [x] AG1 真实任务冒烟 ×2（正常 + 错误路径）：正常路径事件流 turn_start→工具→流式答复→turn_end→[DONE]，hello.py 创建并运行验证；错误路径 execute_command exit_code=1 失败信号正确、[DONE] 仍收尾
- [x] AG2 CLI/REPL/会话/保存/滚动旧功能回归：pytest 98 全绿、compileall、--help、REPL /quit、Web 端点测试
- [x] AG3 证据入 AGENT_LOG，CHECKLIST 迭代 7 全勾选放行

## AH. 迭代 8 切片 8.0 工具扩展 web_search

- [x] AH1 `agent/tools/search_tools.py`：标准库 urllib + html.parser，默认 DuckDuckGo lite（无 key，html 端点被拦时已切换），SEARCH_API_URL/SEARCH_API_KEY 可插拔
- [x] AH2 `web_search` 注册进工具表（7 工具）；SYSTEM_PROMPT 提及；摘要截断/超时/错误观测
- [x] AH3 测试：解析（html+两种布局）/缺 query/请求失败/条数钳制/模板 override/空结果；真实外网冒烟成功（python.org/W3Schools 结果）

## AI. 迭代 8 切片 8.1 goal 模式

- [x] AI1 长目标续跑 + 显式 DONE（「完成」开头）/「受阻：」终止 + 连续 3 轮无进展 blocked 事件；goal 与 reflect 互斥（goal 优先）
- [x] AI2 goal 状态持久化（`SessionStore.update_goal`）+ 恢复 open 会话注入中断上下文（先验证副作用、只重试幂等操作）
- [x] AI3 前端受阻 warn 块 + 状态指示（目标执行中…/推进中…/受阻）；测试（完成/受阻/停滞 ×3 + 恢复注入 + 持久化）；CLI `--goal` + `.env.example`
- [x] AI4 `/goal` 斜杠命令：前端解析 `/goal <任务>` 按次开启 goal 模式（`goal=1` 参数）；空命令占位符提示；goal 持久化仅在 goal 模式/恢复 open 会话时写入

## AJ. 迭代 8 切片 8.2 todo 任务清单

- [x] AJ1 `todo_write` 工具（全量覆盖/status 校验/≤30 项/内容截断）+ `todo` 事件快照（成功后发出）
- [x] AJ2 前端「📋 任务清单」块（☑/▶/☐ 行 + 完成/总数 meta；原位更新不重复）；随 trace 持久化重放可见
- [x] AJ3 测试（工具快照/非法列表/上限/状态归一化 + loop 事件 + DOM 垫片）

## AK. 迭代 8 切片 8.3 subagent 工具

- [ ] AK1 `delegate_subagent {task}`：子线程独立 run、短预算、不可再委托、摘要回填
- [ ] AK2 事件 subagent_start/end + 前端嵌套轨迹块；并行复用工具并行执行
- [ ] AK3 测试（返回/失败回填/并行）

## AL. 迭代 8 切片 8.4 上下文压缩

- [ ] AL1 `compact_history`：超预算先 LLM 总结旧轮次再裁剪；compact 事件（前后 token 数）
- [ ] AL2 前端「上下文压缩」折叠块；失败回退旧截断
- [ ] AL3 测试（触发/不触发/回退）

## AM. 迭代 8 切片 8.5 集成回归

- [ ] AM1 真实冒烟 ×3~4（goal 完成/受阻、todo+subagent 复合、web_search）
- [ ] AM2 全量回归（pytest/CLI/REPL/会话/轨迹）
- [ ] AM3 证据入 AGENT_LOG，迭代 8 放行
