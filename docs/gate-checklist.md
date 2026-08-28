# gate-checklist.md — 迭代 6 · 切片 6.1 放行清单

> 当前阶段：迭代 6 · 切片 6.1（极简 Web 终端）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 标准库 HTTP 服务（零新依赖）：`GET /` 表单页 + `POST /run` 返回输出
- [x] `run_task_output` 捕获过程日志与最终答复
- [x] 本地起服务 → POST 真实任务 → 输出完整
- [x] `pytest -q` 免 key 全绿

## 证据位置

- 测试与冒烟：见 `docs/AGENT_LOG.md` 迭代 6 切片 6.1 条目
- 代码：`agent/web.py`、`tests/test_web.py`

## 退出决定

- 通过 → 切片 6.2（SSE 流式）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
