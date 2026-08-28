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

- [ ] D1 主循环过程可读：展示每步工具调用与结果摘要
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
