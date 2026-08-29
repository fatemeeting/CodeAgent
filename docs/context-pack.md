# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 7 · 切片 7.4-UI2（整体色调与布局细节，模仿 DSH design-platform）**

## 当前阶段目标

仅改 `agent/web.py` 的 CSS/HTML：色调切 DSH 冷调（页面 #f5f6f7、面板 #fff、近黑 #0f1115、三级灰 #81858c、极浅边框 rgba(0,0,0,.04)、代码底 #f9fafb、DeepSeek 蓝 #4176e6 替代橙、状态色 #22c55e/#ef4444/#f59e0b）；布局轻量化（顶栏/输入区极浅分隔、会话按钮无边框轻按钮、chip 浅灰、分隔条 1px 细线 hover 蓝、树/最近 hover 浅蓝底）；对话质感（agent 答复纯文本化、输入框白底 16px 圆角 + 蓝色聚焦光晕、角色标签 caption 灰）。布局结构（三栏）不变。

## 必须读

- `SPEC.md` 第 22 节（本切片范围）
- `agent/web.py`（`:root` 令牌与全部 CSS 选择器）
- 参考（临时克隆）：`%TEMP%\dsh-desktop\deepseek-harness\packages\client\ui-theme\src\styles\design-platform.css`

## 不得读 / 不得改

- `.env`（真实凭据）
- 后端与 JS 逻辑（只读，本切片纯 CSS/HTML）

## 输出要求

- 产出：`agent/web.py`（CSS/HTML 微调）
- 验收：`pytest -q` 全绿（84）；`node --check`；色调/布局标记冒烟；DOM 垫片回归
