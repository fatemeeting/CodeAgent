# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 6 · 切片 6.5（原生文件夹选择器）**

## 当前阶段目标

Web 端「📂 选择」按钮 → `POST /pick-workspace` → 服务端 tkinter（标准库，零新依赖）唤起系统原生文件夹选择对话框 → 返回路径填入工作区输入框；无图形环境时优雅降级（返回错误提示，手动输入兜底）。

## 必须读

- `SPEC.md`（迭代 6 增补 5）
- `agent/web.py`（`do_POST` / `INDEX_HTML`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/web.py`（`pick_workspace` + `/pick-workspace` + 前端按钮）、`tests/test_web.py`（+1）
- 验收：`pytest -q` 全绿；端点 mock 冒烟
