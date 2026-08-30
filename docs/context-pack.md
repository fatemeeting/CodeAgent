# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 9 · 切片 9.2（技能显式注入与命令）**

## 当前阶段目标

`run(skills=)` 仅注入**显式传入**的技能（system 追加 `skill_prompt` 片段；chat 模式过滤 modes）；`/events` 增 `skill` 参数（逗号分隔多技能、未知名/模式不符容错忽略）；`skill_loaded {name, description}` 事件随 run 发出；CLI `--skill NAME`（可重复）+ `--list-skills`（无需 key，先于配置加载输出）。不做自动匹配（`match_skills` 仅预留）。

## 必须读

- `SPEC.md` 第 30 节（含计划修订）、`CHECKLIST.md` AP 节
- `agent/skills.py`（`load_skills`/`skill_prompt`/`Skill`）、`agent/loop.py`（`run` system 构建与事件点）、`agent/cli.py`、`agent/web.py`（`_handle_events` worker）
- `tests/test_loop.py`、`tests/test_web.py`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/loop.py`、`agent/web.py`、`agent/cli.py`、`tests/test_loop.py`、`tests/test_web.py`
- 验收：`pytest -q` 全绿（约 139）；CLI `--list-skills`/`--skill` 冒烟；`node --check`（前端未改，回归确认）
