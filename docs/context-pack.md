# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 9 · 切片 9.3（事件与技能管理 UI）**

## 当前阶段目标

前端「📚 技能装载」note 块（`skill_loaded` 事件，重放可见）；技能管理端点 `GET /skills`（列表，含 source 只读标注）、`POST /skills`（工作区级新建）、`PUT /skills/<name>`（工作区级更新）、`DELETE /skills/<name>`（工作区级删除，路径越界防护）；`/skills` 命令浮层（浏览/选择/✎编辑/🗑删除/只读标签）+ 顶栏「📚 技能」入口。内置（builtin）与 SKILLS_DIR（env）技能只读，仅工作区级可增删改。CRUD 即文件操作（写入/删除 `<workdir>/.codeagent/skills/<name>/SKILL.md`）。

## 必须读

- `SPEC.md` 第 30 节第 3 条（生命周期）、`CHECKLIST.md` AQ 节
- `agent/skills.py`（`load_skills`/`skill_summary`/`workspace_skills_dir`，本切片新增 save/update/delete 助手）
- `agent/web.py`（`do_GET/do_POST/do_DELETE` 路由、`handleEvent`、`parseCommand`/`sendTask`/`CMD_ITEMS`、`#modal` 弹层、顶栏）
- `tests/test_skills.py`、`tests/test_web.py`（Web 端点与 DOM 垫片模式）

## 不得读 / 不得改

- `.env`（真实凭据）
- 内置 `skills/`（9.4 才添加，本切片不碰）

## 输出要求

- 产出：`agent/skills.py`、`agent/web.py`、`tests/test_skills.py`、`tests/test_web.py`
- 验收：`pytest -q` 全绿（约 150）；`python -m compileall agent`；`node --check`（前端改动）；真实服务冒烟（GET/POST/PUT/DELETE /skills + 列表只读标注）
