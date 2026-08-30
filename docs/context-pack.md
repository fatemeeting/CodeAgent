# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 8 · 切片 8.2（todo 任务清单：todo_write 工具 + todo 事件 + 进度 UI）**

## 当前阶段目标

新增 `todo_write` 工具（模型维护全量清单 `[{id, content, status}]`，status ∈ pending/in_progress/completed，≤30 项、内容 100 字截断，返回简短确认）；loop 在清单更新且执行成功时发 `todo` 事件（全量快照）；前端轨迹区渲染「📋 任务清单」块（☑/▶/☐ 状态行 + `完成/总数` meta，后续事件原位更新不重复建块）；清单随 trace 持久化重放可见；SYSTEM_PROMPT 提及。

## 必须读

- `SPEC.md` 第 27 节切片 8.2
- `agent/tools/__init__.py`（注册）、`agent/loop.py`（观测回填循环与事件点）、`agent/web.py`（`handleEvent`/`newTurnState`/`.tblk` CSS）
- `tests/test_tools.py`、`tests/test_loop.py`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/tools/todo_tools.py`、`agent/tools/__init__.py`、`agent/loop.py`、`agent/web.py`、测试
- 验收：`pytest -q` 全绿（约 117）；`node --check`；DOM 垫片（清单块/原位更新/重放）；冒烟标记
