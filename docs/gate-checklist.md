# gate-checklist.md — 阶段 3 放行清单

> 当前阶段：阶段 3（闭环循环）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `parser.py` 正确分流文本与 tool_calls；arguments 解析含异常兜底
- [x] 模型无 tool_calls 时循环终止并返回文本（CHECKLIST A10）
- [x] 模型有 tool_calls 时执行、回填、再次调用模型（CHECKLIST A9）
- [x] 达到 `--max-iterations` 上限时终止并说明（CHECKLIST A11）
- [x] 工具执行异常回填为观测，不中断循环（错误处理）
- [x] `--workdir` 生效（工具在工作目录内执行）
- [x] `pytest -q` 免 key 全绿
- [x] 真实任务「创建 hello.py 并运行输出」闭环（CHECKLIST A12）

## 证据位置

- 测试输出与端到端冒烟：见 `docs/AGENT_LOG.md` 阶段 3 条目
- 代码：`agent/parser.py`、`agent/loop.py`、`agent/cli.py`、`tests/test_parser.py`、`tests/test_loop.py`

## 退出决定

- 通过 → 进入阶段 4（上下文管理）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
