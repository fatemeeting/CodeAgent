---
name: code-review
description: 代码评审规范：红线核对、最小 diff、契约一致、证据驱动，结论写入 AGENT_LOG
keywords: 评审, review, 审查, 代码质量, 红线, diff, 契约
modes: agent, chat
---
# 代码评审规范

## 评审顺序
1. **红线核对**：无新依赖（本仓库仅允许 openai）；无密钥入库（git grep 扫描 + .env gitignore）；无 rm -rf / git push --force / 生产环境等危险操作。
2. **最小 diff**：一次一个功能切片；无整文件重写；无关文件零改动；改动可独立回退。
3. **契约一致**：SPEC / CHECKLIST 与代码行为一致；新功能有对应验收项、测试与证据。
4. **回归**：旧功能（CLI / REPL / Web / 会话）零回归；空状态与窄屏不破坏。

## 结论格式
- 先给结论：通过 / 有条件通过 / 不通过。
- 问题按严重度分级：阻断（必须修）/ 建议（可改进），每条给出文件、行号与最小修复建议。
- 证据清单：`pytest -q`、`compileall`、`git status --ignored`、密钥扫描输出、真实冒烟记录。

## 落库要求
- 评审范围 / 结论 / 发现与处置 / 放行决定四要素写入 `docs/AGENT_LOG.md`。
- 未过 Checklist 不放行；证据不足不视为完成；连续失败缩小范围或人工接管。
