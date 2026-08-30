# gate-checklist.md — 迭代 9 · 切片 9.4 放行清单

> 当前阶段：迭代 9 · 切片 9.4（内置技能）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 三个内置技能 SKILL.md（frontmatter 合法、正文 ≤4000、来源标注 builtin 只读）
- [x] 显式装载生效（CLI --skill、/events?skill、/skill 命令）；未指定技能不自动装载
- [x] 受影响断言更新（GET /skills 列表含内置；内置不可删除）；`pytest -q` 全绿
- [x] 真实冒烟：显式装载 python-testing，答复体现规范；CLI --list-skills 显示内置

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 9 切片 9.4 条目
- 代码：`skills/*/SKILL.md`、`tests/test_web.py`、`tests/test_skills.py`、`agent/cli.py`、`agent/web.py`（stdio 加固）

## 退出决定

- 通过 → 切片 9.5（集成回归）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
