# gate-checklist.md — 迭代 5 · 切片 5.3 放行清单

> 当前阶段：迭代 5 · 切片 5.3（human-in-the-loop）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `is_dangerous` 识别危险命令（rm / del / git push 等），不误伤普通命令
- [x] `--confirm` 危险命令前请求确认；拒绝则不执行并回填「已取消」
- [x] 确认（y）后正常执行
- [x] 未开启 confirm 时行为不变（不回归）
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 5 切片 5.3 条目
- 代码：`agent/tools/shell_tools.py`、`agent/config.py`、`agent/loop.py`、`agent/cli.py`

## 退出决定

- 通过 → 迭代 5 完成
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
