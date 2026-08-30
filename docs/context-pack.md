# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 9 · 切片 9.1（技能存储与解析）**

## 当前阶段目标

新建 `agent/skills.py`：`Skill` 数据类 + `SKILL.md` 轻量 frontmatter 解析（name/description/keywords/modes + 正文，零新依赖，坏文件容错跳过，正文 4000 字截断）；三级目录合并（内置 `skills/` < `SKILLS_DIR` < 工作区 `<workdir>/.codeagent/skills`，就近覆盖去重）；`match_skills`（关键词 +3/描述词 +1 得分、上限 2、modes 过滤）；`skill_prompt` 注入片段。

## 必须读

- `SPEC.md` 第 30 节（迭代 9 计划）
- `agent/skills.py`（新建）、参考 `agent/tools/base.py`（dataclass 风格）
- `tests/test_skills.py`（新建）

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/skills.py`、`tests/test_skills.py`
- 验收：`pytest -q` 全绿（约 132）；`compileall`
