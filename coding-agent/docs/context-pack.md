# context-pack.md — 当前阶段上下文包

> 当前阶段：**阶段 1（骨架冒烟）**

## 当前阶段目标

搭建 `agent/` 包骨架，实现 `config.py`（自研 .env 加载）+ `llm.py`（DeepSeek 封装 + 自研重试）+ 最小 `loop.py`（发消息→打印回复，无工具），跑通「能启动、能访问 API、无基础错误」。

## 必须读

- `SPEC.md`（阶段划分与技术约束）
- `CHECKLIST.md`（A1 / A2 项）
- `AGENTS.md`（禁止事项与检查命令）
- `docs/AGENT_LOG.md`（阶段 0 已完成事实）

## 可读（按需）

- `docs/context-snapshot.md`
- `.env.example`（变量名参考，不读真实 `.env`）

## 不得读 / 不得改

- `.env`（真实凭据，仅由 `config.py` 运行时加载，人工不得查看其值）
- 已推送的 Git 历史

## 输出要求

- 只产出阶段 1 约定文件：`agent/` 包（`__init__` / `config` / `llm` / `loop` / `cli` / `__main__`）
- 完成后给出可观察证据：`python -m agent --help` 与真实「你好」冒烟输出
