# gate-checklist.md — 迭代 9 · 切片 9.3 放行清单

> 当前阶段：迭代 9 · 切片 9.3（事件与技能管理 UI）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 前端「📚 技能装载」note 块（skill_loaded 事件；trace 重放可见）
- [x] `GET/POST/PUT/DELETE /skills`：工作区级 CRUD、名称校验与路径越界防护、builtin/env 只读标注
- [x] `/skills` 命令浮层（浏览/选择/✎编辑/🗑删除/只读标签）+ 顶栏「📚 技能」入口
- [x] `pytest -q` 全绿（144）；`compileall`；`node --check`；真实服务冒烟（CRUD + 只读标注）

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 9 切片 9.3 条目
- 代码：`agent/skills.py`、`agent/web.py`、`tests/test_skills.py`、`tests/test_web.py`

## 退出决定

- 通过 → 切片 9.4（内置技能）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
