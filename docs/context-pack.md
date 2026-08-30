# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 9 · 切片 9.4（内置技能）**

## 当前阶段目标

新增三个内置技能（随发行、只读）：`skills/python-testing`（pytest 测试规范）、`skills/code-review`（评审规范）、`skills/web-frontend`（前端零依赖规范）。每个 = 目录 + `SKILL.md`（frontmatter name/description/keywords/modes + 正文 ≤4000 字）。技能仍**仅显式指定装载**（/skill 命令、CLI --skill、/events?skill），不接入自动匹配。更新受影响断言（`GET /skills` 列表现在含 builtin 技能；内置不可删除）。

## 必须读

- `SPEC.md` 第 30 节、`CHECKLIST.md` AR 节（AR2 已按「仅显式」修订）
- `agent/skills.py`（`_parse_skill`/`load_skills`/`_load_dir`）、`agent/cli.py`（--list-skills）
- `tests/test_skills.py`（merge 优先级）、`tests/test_web.py`（`test_web_skills_crud` 初始列表断言）

## 不得读 / 不得改

- `.env`（真实凭据）
- 9.3 的 CRUD 端点与浮层（已放行，不重改）

## 输出要求

- 产出：`skills/python-testing/SKILL.md`、`skills/code-review/SKILL.md`、`skills/web-frontend/SKILL.md`；`tests/test_web.py` 断言更新
- 验收：`pytest -q` 全绿（约 146）；CLI `--list-skills` 显示 3 个内置（免 key）；真实冒烟显式装载 python-testing，答复体现规范
