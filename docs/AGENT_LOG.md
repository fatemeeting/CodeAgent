# AGENT_LOG.md — 开发日志与放行记录

> 记录：阶段名与时间、给 Agent 的任务、Agent 修改了什么、检查证据、人工放行决定。

## 阶段 0：契约先行

- **时间**：2026-08-28 10:42（开始）
- **给 Agent 的任务**：按 agentos-coding-standards 产出 SPEC / CHECKLIST / AGENTS 与工程基础文件（.gitignore / .env.example / requirements.txt）及契约工作文件。
- **Agent 修改了什么**：新建 `SPEC.md`、`CHECKLIST.md`、`AGENTS.md`、`.gitignore`、`.env.example`、`requirements.txt`，以及 `docs/` 下 `AGENT_LOG.md`、`context-pack.md`、`context-snapshot.md`、`gate-checklist.md`、`prompts/stage-template.md`。
- **检查证据**：见 `docs/gate-checklist.md` 的逐项勾选。
- **人工放行决定**：通过（用户继续推进，要求先建虚拟环境）

## 环境准备（阶段 0 补充）

- **时间**：2026-08-28
- **给 Agent 的任务**：创建虚拟环境 `.venv`
- **Agent 修改了什么**：`python -m venv .venv`（Python 3.11.9，pip 24.0）
- **检查证据**：`python --version` → 3.11.9；`.venv\Scripts\python.exe -m pip --version` → pip 24.0
- **人工放行决定**：通过

## 依赖安装（阶段 0 补充）

- **时间**：2026-08-28
- **给 Agent 的任务**：编写 environment 文件汇总全部依赖，并安装到 `.venv`
- **Agent 修改了什么**：
  - `requirements.txt`：运行时依赖，锁定 `openai==3.3.1`
  - `requirements-dev.txt`：`-r requirements.txt` + `pytest==9.1.1`
  - `requirements.lock`：`pip freeze` 完整锁定 20 个包（含传递依赖）
  - 安装命令：`pip install -r requirements-dev.txt -i https://mirrors.aliyun.com/pypi/simple`（PyPI 直连在本沙箱超时，故用国内镜像）
- **检查证据**：
  - `pip check` → 无冲突（EXIT=0）
  - `import openai` / `from openai import OpenAI` → 正常，`openai.__version__` = 3.3.1
  - 关键包：openai 3.3.1、pytest 9.1.1、pydantic 2.13.4、httpx2 2.12.0、jiter 0.16.0
- **风险备注**：openai 已到 3.x（底层用 httpx2/httpcore2），阶段 1 写 `llm.py` 时需验证 `chat.completions.create` 与 tool calling 参数名在 3.x 下是否兼容
- **人工放行决定**：通过

## 阶段 1：骨架冒烟

- **时间**：2026-08-28
- **给 Agent 的任务**：按 A 方案（自研 .env 解析）搭建 `agent/` 包骨架，实现最小「发消息→打印回复」，跑通真实冒烟
- **Agent 修改了什么**：
  - `agent/__init__.py`（`__version__ = "0.1.0"`）
  - `agent/config.py`：`Config` 数据类 + 自研 `load_dotenv`（支持 `KEY=VALUE`/`export`、注释、环境变量优先，不引入 python-dotenv）
  - `agent/llm.py`：`LLMClient`（`OpenAI(api_key, base_url)`）+ 自研指数退避重试 + `LLMError`
  - `agent/loop.py`：最小主循环（system + user 消息 → 打印回复）
  - `agent/cli.py` / `agent/__main__.py`：argparse 入口（`task`、`--model`、`--max-iterations`）
  - 更新 `docs/context-pack.md`、`docs/gate-checklist.md` 到阶段 1
- **检查证据**：
  - openai 3.x API 内省：`OpenAI(api_key, base_url)`、`chat.completions.create(..., tools=, tool_choice=)` 参数均存在
  - `python -m compileall -q agent` → EXIT=0
  - `python -m agent --help` → 正常显示中文用法，EXIT=0
  - `python -m agent "你好"` → 返回「你好！很高兴为你提供编程帮助。有什么可以帮你的吗？」，EXIT=0（真实 DeepSeek 调用）
- **风险处置**：openai 3.x 兼容性风险已解除（实测构造参数与 tool calling 参数名兼容）
- **人工放行决定**：通过

## 阶段 2：工具层

- **时间**：2026-08-28
- **给 Agent 的任务**：实现六个本地工具 + JSON Schema + 注册表，mock 单测验证「工具名 → 参数 → 处理函数」映射
- **Agent 修改了什么**：
  - `agent/tools/base.py`：`Tool`（name/description/parameters/handler + `to_schema`）、`resolve_path`、`Handler` 类型
  - `agent/tools/file_tools.py`：`read_file`（UTF-8 + 100KB 截断）、`write_file`（自动建父目录）、`edit_file`（多处匹配需 `replace_all`）
  - `agent/tools/shell_tools.py`：`execute_command`（subprocess + 超时 + 输出截断 + stdout/stderr/退出码）
  - `agent/tools/fs_tools.py`：`list_directory`、`search_content`（递归 + 跳过 .git/.venv 等 + 上限 200 条）
  - `agent/tools/__init__.py`：`TOOLS` 注册表 + `tool_schemas()` + `dispatch()`
  - `tests/test_tools.py`（10 用例）、`conftest.py`（sys.path 注入）
  - 更新 `docs/context-pack.md`、`docs/gate-checklist.md` 到阶段 2
- **检查证据**：
  - `python -m pytest -q` → **10 passed in 0.28s**，EXIT=0（全程免 key）
  - execute_command 的 subprocess 管道捕获在沙箱正常（`echo hello`、`sys.exit(3)` 均验证）
- **风险处置**：无
- **人工放行决定**：通过

## CI/CD 基础设施（阶段 2 补充）

- **时间**：2026-08-28
- **给 Agent 的任务**：补齐测试覆盖（config/llm），搭建 git 仓库 + pre-commit 钩子 + GitHub Actions CI
- **Agent 修改了什么**：
  - `tests/test_config.py`（4 用例：.env 解析、默认值、缺 key 报错）、`tests/test_llm.py`（3 用例：返回、重试耗尽抛 LLMError、重试后成功）
  - `scripts/gate_check.py`（pre-commit：拦 .env + 扫 `sk-` 密钥 + 查 gate 文件）、`scripts/commit_msg_check.py`（提交信息含阶段名）、`scripts/install_hooks.py`
  - `.github/workflows/ci.yml`（compileall + pytest，mock 免 key）
  - `git init`（分支 main）+ 分阶段提交：`bf400e5` 阶段0-2、本提交 CI/CD
  - 更新 `AGENTS.md`（第 6 节 CI/CD 与提交规范）
- **检查证据**：
  - `python -m pytest -q` → **17 passed**（10 工具 + 4 config + 3 llm）
  - 提交树校验：`.env` / `.venv` 未被跟踪
  - gate_check 直测 exit 0；密钥正则命中真实 key、不误伤占位符；commit_msg 合法→0 / 非法→1
- **风险备注**：本沙箱限制了 Git Bash 的共享内存（`sh.exe CreateFileMapping error 5`），shell 包装的钩子在此沙箱内无法端到端运行，但 Python 逻辑已直测通过；在正常机器与 GitHub Actions 上钩子可正常生效
- **人工放行决定**：通过

## 阶段 3：闭环循环

- **时间**：2026-08-28
- **给 Agent 的任务**：实现完整主循环（解析 / 工具回填 / 终止条件 / 错误处理），mock 单测 + 真实端到端冒烟
- **Agent 修改了什么**：
  - `agent/parser.py`：`parse_response` 分流文本与 tool_calls；`_parse_arguments` 防御式 JSON 解析（非法 JSON 回填 `_error`）
  - `agent/loop.py`：完整循环——无 tool_calls 即终止返回；有则重建 assistant/tool 消息并回填；`--max-iterations` 上限；工具异常回填为观测；观测截断（4000 字符）
  - `agent/cli.py`：新增 `--workdir`
  - `tests/test_parser.py`（4 用例）、`tests/test_loop.py`（4 用例）
  - 更新 `docs/context-pack.md`、`docs/gate-checklist.md`
- **检查证据**：
  - `pytest -q` → **25 passed**（17 旧 + 4 parser + 4 loop）
  - 真实端到端：`python -m agent "创建 hello.py 并运行" --workdir $TEMP\agent-smoke` → 生成 hello.py、运行输出 `Hello from agent`、EXIT=0
  - 独立核验：hello.py 内容 `print('Hello from agent')`，亲自运行输出 `Hello from agent`
- **风险处置**：无
- **人工放行决定**：通过

## GitHub 远程与 CI 验证（阶段 3 后续）

- **时间**：2026-08-28
- **给 Agent 的任务**：找到用户远程仓库、推送本地工作、让 CI 运转
- **Agent 做了什么**：
  - 定位远程：SSH 认证为 `fatemeeting`（初时用户名误拼 `fatemeeeting` 导致 API/仓库 404，后按用户 URL 修正为 `fatemeeting`）
  - `git remote add origin git@github.com:fatemeeting/CodeAgent.git`；用 `GIT_SSH` 绕过沙箱 `sh` 限制完成 fetch/push
  - **根因**：GitHub 旧历史把项目嵌在 `coding-agent/` 子目录，GitHub Actions 不会自动检测子目录 `.github/workflows/*.yml` → CI 不跑
  - 按用户决定用本地正确根目录结构替换 main；旧嵌套历史备份到 `backup/original-nested`（未丢失）
  - 仓库由用户改为公开
- **检查证据**：
  - `api.github.com/repos/fatemeeting/CodeAgent` → private=False, default_branch=main
  - Actions runs：`CI` status=completed, **conclusion=success**（2026-08-28T08:18Z）
- **人工放行决定**：通过

## 阶段 4：上下文管理

- **时间**：2026-08-28
- **给 Agent 的任务**：自研 token 估算与历史截断，接入主循环与 `--max-context-tokens`
- **Agent 修改了什么**：
  - `agent/context.py`：`estimate_tokens`（ASCII≈4 字符/token、CJK≈1 字符/token）+ `truncate_history`（保留 system + 首条 user + 最近消息，丢弃孤儿 tool 消息以保证配对）
  - `agent/config.py`：新增 `max_context_tokens`（默认 12000，读 `DEEPSEEK_MAX_CONTEXT_TOKENS`）
  - `agent/loop.py`：每次调用模型前 `truncate_history`
  - `agent/cli.py`：新增 `--max-context-tokens`
  - `.env.example`：新增 `DEEPSEEK_MAX_CONTEXT_TOKENS`
  - `tests/test_context.py`（7 用例）
  - 更新 `docs/context-pack.md`、`docs/gate-checklist.md`
- **检查证据**：
  - `pytest -q` → **32 passed**（25 旧 + 7 context）
  - `python -m agent --help` 显示 `--max-context-tokens`
  - `compileall -q agent` → EXIT=0
- **风险处置**：token 估算是启发式（不引入 tokenizer，留安全余量）；孤儿 tool 消息已做配对保护
- **人工放行决定**：通过

## 阶段 5：集成回归

- **时间**：2026-08-28
- **给 Agent 的任务**：跑 2–3 个真实任务回归，核对旧功能不回退；同步 CHECKLIST 进度
- **Agent 修改了什么**：无代码改动（纯回归）；更新 `docs/context-pack.md`、`docs/gate-checklist.md`、`CHECKLIST.md`（勾选）
- **检查证据**：
  - 回归任务 1（写+执行）：创建 `calc.py` + 验证 `add(2,3)==5` → 闭环，EXIT=0
  - 回归任务 2（改+验证）：`add`→`multiply` + 验证 `multiply(2,3)==6` → 闭环，EXIT=0
  - 回归任务 3（列+搜索）：`list_directory` 找到 `calc.py`；`search_content` 命中 `calc.py:1 def multiply(a, b):` → 闭环，EXIT=0
  - 独立核验：`calc.py` 内容正确、独立运行输出 `6`
  - `pytest -q` → **32 passed**（无回退）
  - B4 无被禁依赖（grep 无命中）；C1 无真实密钥（`git grep sk-[A-Za-z0-9]{24,}` 无命中）
- **风险处置**：无（3 个任务全过，无失败项）
- **人工放行决定**：（待用户确认：通过 / 重试 / 降级 / 停止）
