# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 6 v2 · 切片 6.6（工作区管理器 + 视觉系统）**

## 当前阶段目标

重写 Web 端为 Cursor 风格（B 策略：编辑器用 CDN Monaco，本切片暂不加载）：暖白视觉系统（#f7f7f4 / #26251e / #f54e00、8px 间距）；**专用工作区管理器**（选择：原生对话框/手动输入/最近列表；确认：显式按钮 + `GET /tree` 校验；管理：localStorage 最近列表 + 顶栏 🔄 切换弹层）；未选工作区只显示管理器，其余内容隐藏。主布局骨架（顶栏 + 双栏占位）本切片就位。

## 必须读

- `SPEC.md`（迭代 6 增补 6）
- `agent/web.py`（`do_GET` / `INDEX_HTML`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/web.py`（`_workspace_tree` + `GET /tree` + `INDEX_HTML` 重写）、`tests/test_web.py`（+1）
- 验收：`pytest -q` 全绿；冒烟（欢迎页标记 / tree 校验 / 主布局骨架）
