# gate-checklist.md — 阶段 2 放行清单

> 当前阶段：阶段 2（工具层）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [x] 六个工具注册齐全（read_file / write_file / edit_file / execute_command / list_directory / search_content）
- [x] 每个工具 schema 合法：type=function、有 name/description、parameters.type=object、required ⊆ properties
- [x] `python -m pytest -q` 免 key 全绿（CHECKLIST B1）
- [x] read/write/edit 往返正确；edit 多处匹配需 replace_all
- [x] execute_command 有超时、捕获 stdout/stderr/退出码（CHECKLIST A6、C3）
- [x] dispatch 未知工具返回错误观测

## 证据位置

- 测试输出：见 `docs/AGENT_LOG.md` 阶段 2 条目
- 代码：`agent/tools/*`、`tests/test_tools.py`

## 退出决定

- 通过 → 进入阶段 3（闭环循环）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
