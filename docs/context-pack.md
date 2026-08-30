# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 9 · 切片 9.5（集成回归）**

## 当前阶段目标

迭代 9 收尾回归：全量 pytest + compileall + CLI/REPL/Web 端点回归 + 前端 node --check 与无头垫片；真实冒烟覆盖「显式 /skill + chat 模式共存」（chat 仅装载 modes 含 chat 的技能、agent-only 技能被过滤、未指定不自动装载）与「会话/技能 CRUD 共存」。失败项定位到具体切片，只修该切片；证据入 AGENT_LOG 后放行迭代 9。

## 必须读

- `SPEC.md` 第 30 节、`CHECKLIST.md` AO–AS 节（AS2 已按「仅显式」修订）
- `docs/AGENT_LOG.md` 迭代 9 各切片条目（9.1–9.4）
- `agent/web.py`（/events worker、/skills 端点）、`agent/cli.py`（--skill/--list-skills/_harden_stdio）

## 不得读 / 不得改

- `.env`（真实凭据）
- 已放行切片代码（9.1–9.4），回归失败才允许最小修复

## 输出要求

- 产出：契约文件勾选 + `docs/AGENT_LOG.md` 迭代 9 总结
- 验收：`pytest -q` 全绿（146）；compileall/--help/REPL /quit；node --check + 垫片冒烟；真实冒烟 ×2（chat+skill 共存、CRUD 共存）；迭代 9 放行
