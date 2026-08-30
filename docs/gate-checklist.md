# gate-checklist.md — 迭代 7 · 切片 7.5 修复 3 放行清单

> 当前阶段：迭代 7 · 切片 7.5 修复 3（工作区物理分层 + 中断轮次标记）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `data/sessions/<ws-slug>/<id>.json` 物理分层；旧平铺文件初始化自动迁移；兼容读取（旧文件未迁移成功仍可读）
- [x] 重放末轮无 `turn_end` → 追加 `turn_end{interrupted}` → 琥珀「上次中断」行；error severity=warn 琥珀分级
- [x] `pytest -q` 全绿（98）；`node --check`；DOM 垫片；冒烟标记

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 7 切片 7.5 修复 3 条目
- 代码：`agent/sessions.py`、`agent/web.py`、`tests/test_sessions.py`

## 退出决定

- 通过 → 切片 7.6（集成回归）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
