# context-pack.md — 当前阶段上下文包

> 当前阶段：**阶段 2（工具层）**

## 当前阶段目标

实现六个本地工具（read_file / write_file / edit_file / execute_command / list_directory / search_content）的 JSON Schema 与本地执行，建立工具注册表；用 mock 单测验证「工具名 → 参数 → 处理函数」映射正确，全程免 key。

## 必须读

- `SPEC.md`（范围：六个工具；技术约束：本地执行、带超时）
- `CHECKLIST.md`（A3–A8、B1、C3 项）
- `AGENTS.md`（禁止事项：execute_command 限制 workdir、必须带超时）
- `docs/context-snapshot.md`（阶段 1 已完成事实）

## 可读（按需）

- `agent/config.py`（workdir 将在阶段 3 来自 Config/CLI）
- `.env.example`

## 不得读 / 不得改

- `.env`（真实凭据）
- 阶段 1 已放行的代码（除非必要最小修改）

## 输出要求

- 只产出阶段 2 约定文件：`agent/tools/`（`base` / `file_tools` / `shell_tools` / `fs_tools` / `__init__`）、`tests/test_tools.py`、`conftest.py`
- 验收：`python -m pytest -q` 全程免 key 通过
