# gate-checklist.md — 迭代 9 · 切片 9.1 放行清单

> 当前阶段：迭代 9 · 切片 9.1（技能存储与解析）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `Skill` 模型 + frontmatter 解析（description/keywords/modes/正文；坏文件跳过；4000 字截断）
- [x] 三级目录合并与就近覆盖去重；`workspace_skills_dir` 路径
- [x] `match_skills`：得分排序、上限 2、modes 过滤；`skill_prompt` 注入片段
- [x] `pytest -q` 全绿（135）；`compileall`

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 9 切片 9.1 条目
- 代码：`agent/skills.py`、`tests/test_skills.py`

## 退出决定

- 通过 → 切片 9.2（注入与命令）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
