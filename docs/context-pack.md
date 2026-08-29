# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 7 · 切片 7.2 体验修复 6（步骤观测乱码）**

## 当前阶段目标

步骤观测乱码：`execute_command` 单一 `encoding="utf-8"` 解码导致 Windows 控制台代码页（GBK/CP936）输出变 `�`。改为字节捕获 + `_decode` 回退链（UTF-8 优先 → `locale.getpreferredencoding` → 容错替换），stdout/stderr 分别解码。

## 必须读

- `SPEC.md` 第 19 节（本切片范围）
- `agent/tools/shell_tools.py`（`execute_command` / `_truncate`）
- `tests/test_tools.py`（新增 `_decode` 用例）

## 不得读 / 不得改

- `.env`（真实凭据）
- 其余工具与端点（只读）

## 输出要求

- 产出：`agent/tools/shell_tools.py`、`tests/test_tools.py`
- 验收：`pytest -q` 全绿（75）；真实命令冒烟（UTF-8 输出 + 模拟 GBK 字节输出）
