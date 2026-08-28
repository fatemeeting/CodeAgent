# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 6 · 切片 6.3（工作区先行）**

## 当前阶段目标

「先指定工作区，再在指定工作区完成项目」：REPL 新增 `/workdir [路径]`（提示符显示当前工作区）；Web 的 `/run` `/events` 接受 workdir 参数并校验目录存在。

## 必须读

- `SPEC.md`（迭代 6 增补 3/4）
- `agent/repl.py`（`interpret` / `repl`）
- `agent/web.py`（`do_POST` / `_handle_events`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/repl.py`（/workdir + 提示符）、`agent/web.py`（workdir 参数 + 校验）、`tests/test_repl.py`（+2）、`tests/test_web.py`（+1）
- 验收：`pytest -q` 全绿；REPL 与 Web 真实冒烟
