# gate-checklist.md — 迭代 7 · 切片 7.6 放行清单

> 当前阶段：迭代 7 · 切片 7.6（集成回归）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] AG1 真实任务冒烟 ×2：正常路径（创建 hello.py + 运行验证）与错误路径（不存在命令 → exit_code≠0/失败信号），均以 `[DONE]` 收尾
- [x] AG2 回归：`pytest -q` 全绿（98）；`compileall`；`--help`；REPL `/quit`；Web 端点测试
- [x] AG3 证据入 AGENT_LOG；CHECKLIST 迭代 7 全部勾选；放行决定

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 7 切片 7.6 条目

## 退出决定

- 通过 → 迭代 7 完成（迭代 8：对话/轨迹 Tab 全景视图等）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
