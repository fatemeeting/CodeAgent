# gate-checklist.md — 迭代 9 · 切片 9.2 放行清单

> 当前阶段：迭代 9 · 切片 9.2（技能显式注入与命令）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `run(skills=)` 显式注入 system（无自动匹配）；chat 模式过滤 modes；`skill_loaded` 事件
- [x] `/events?skill=a,b` 多技能装载、未知名/模式不符容错
- [x] CLI `--skill NAME`（可重复）/`--list-skills`（免 key）
- [x] `pytest -q` 全绿（139）；CLI 冒烟（--list-skills 显示工作区技能）；回归

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 9 切片 9.2 条目
- 代码：`agent/loop.py`、`agent/web.py`、`agent/cli.py`、测试

## 退出决定

- 通过 → 切片 9.3（事件与技能管理 UI）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
