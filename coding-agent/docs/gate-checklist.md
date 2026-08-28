# gate-checklist.md — 阶段 1 放行清单

> 当前阶段：阶段 1（骨架冒烟）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] `python -m agent --help` 正常显示用法并以 0 退出（CHECKLIST A1）
- [x] `python -m agent "你好"` 返回模型文本回复（CHECKLIST A2）
- [x] `config.py` 自研 `.env` 加载，不引入第三方 dotenv 依赖
- [x] `llm.py` 使用 `OpenAI(api_key, base_url)` + 自研重试，失败抛 `LLMError`
- [x] 无任何 agent 框架 import；`requirements.txt` 仍仅 `openai`

## 证据位置

- 命令输出：见 `docs/AGENT_LOG.md` 阶段 1 条目
- 代码：`agent/config.py`、`agent/llm.py`、`agent/loop.py`、`agent/cli.py`、`agent/__main__.py`

## 退出决定

- 通过 → 进入阶段 2（工具层）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
