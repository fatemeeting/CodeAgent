# gate-checklist.md — 迭代 7 · 切片 7.3 放行清单

> 当前阶段：迭代 7 · 切片 7.3（事件化后端）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `loop.py` emit 回调产出完整事件序列（turn_start → … → turn_end）；emit=None 时 CLI print 行为与改前一致（回归测试）
- [x] `llm.py` 流式捕获 reasoning_content（on_reasoning/on_content 回调，回调模式下不打印）；非流式挂载 response.reasoning
- [x] `config.py` `DEEPSEEK_THINK=1` → model=deepseek-reasoner；显式 DEEPSEEK_MODEL 优先
- [x] `web.py /events` 事件帧（type+text，content_delta 携带正文）；增量流式测试 + 事件序列测试通过
- [x] `pytest -q` 全绿（83）；真实服务冒烟；openai 3.x reasoning_content 透传内省

## 证据位置

- 检查证据：见 `docs/AGENT_LOG.md` 迭代 7 切片 7.3 条目
- 代码：`agent/llm.py`、`agent/loop.py`、`agent/config.py`、`agent/web.py`、`.env.example`

## 退出决定

- 通过 → 切片 7.4（前端内联折叠轨迹块 + 结构化持久化）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
