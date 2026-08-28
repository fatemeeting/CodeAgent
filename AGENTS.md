# AGENTS.md — 编程智能体（Coding Agent）开发约定

> 面向参与本仓库开发 / 评审的 AI 与人类协作者，进入版本控制。

## 1. 项目目标

从零实现一个 Python CLI 编程智能体：用户给任务 → 通过 DeepSeek 大模型自主调用本地工具（读写文件 / 执行命令 / 列目录 / 搜索）→ 循环直至完成。**不用任何 agent 框架，核心逻辑自研。**

## 2. 优先阅读顺序

1. `requirement_doc/推免考核题目学生版.pdf` — 原始题目与规则（唯一权威需求）
2. `SPEC.md` — 做什么、范围、非目标、技术约束
3. `CHECKLIST.md` — 如何验收、需要什么证据
4. `docs/context-pack.md` — 当前阶段要读什么
5. `docs/AGENT_LOG.md` — 已做了什么、证据、放行决定

## 3. 常用检查命令

```bash
python -m pytest -q              # 单元测试（mock LLM，免 key）
python -m compileall agent       # 语法检查
python -m agent --help           # CLI 可用性
python -m agent "你好"           # 真实冒烟（需 DEEPSEEK_API_KEY）
git status --ignored             # 确认 .env 未跟踪
git grep -n "sk-" -- . ':!*.md'  # 扫描疑似密钥（人工核对）
python scripts/install_hooks.py    # 安装 git 钩子（clone 后执行一次）
```

## 4. 禁止事项与安全边界

- ❌ 不引入任何 agent 框架 / SDK；仅允许 `openai` 客户端库
- ❌ 不依赖服务端托管代码执行 / 文件工具（Code Interpreter、Files API）
- ❌ 不读取、不提交密钥；不碰 `.env` 之外的真实凭据文件
- ❌ 不执行 `rm -rf`、`git push --force`、破坏性删除、生产环境操作
- ❌ 不重写整个文件 —— 用最小 diff；一次只做一个功能 / 缺陷切片
- ✅ `execute_command` 限制在 `--workdir`，必须带超时

## 5. 工作流红线

1. 先给计划（步骤 / 涉及文件 / 风险 / 检查方式），人工确认后再改文件
2. 每阶段先写 / 更新 SPEC、CHECKLIST、context-pack，再动代码
3. 每次修改后给出可观察证据（命令输出 / 日志），写入 `docs/AGENT_LOG.md`
4. Checklist 未过不进下一阶段；证据不足不视为完成
5. 失败时缩小范围或降级，不硬撑

## 6. CI/CD 与提交规范

- **本地钩子**：`python scripts/install_hooks.py` 安装
  - `pre-commit`：拦截 `.env` 入库、扫描 `sk-` 密钥、检查 SPEC/CHECKLIST/AGENTS 存在
  - `commit-msg`：提交信息必须包含阶段名（如「阶段3：闭环循环」）
- **CI**：`.github/workflows/ci.yml` 在 push / PR 时执行 `compileall` + `pytest`（mock LLM，免 key）
- **分支**：每阶段 / 功能切片用独立分支，Merge Request 承载人工 review
- **红线**：绝不 `git push --force`；不压缩或改写已推送历史
