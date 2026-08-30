# gate-checklist.md — 迭代 8 · 切片 8.5 放行清单

> 当前阶段：迭代 8 · 切片 8.5（集成回归）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] AM1 真实冒烟：goal 完成（goal_start/goal_end + 产物）、goal 受阻（blocked 或 exit_code≠0）、复合任务（todo + 工具结果）、web_search 复验，均以 [DONE] 收尾
- [x] AM2 回归：`pytest -q` 全绿（123）；`compileall`；`--help`；REPL `/quit`
- [x] AM3 证据入 AGENT_LOG；CHECKLIST 迭代 8 全部勾选；放行决定

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 8 切片 8.5 条目

## 退出决定

- 通过 → 迭代 8 完成
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
