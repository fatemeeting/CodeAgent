# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 6 · 切片 6.4（聊天式 Web 界面，模仿 DeepSeek Harness）**

## 当前阶段目标

把表单页改为对话式布局：消息气泡（用户右 / agent 左）、顶部工作区输入（先指定）、底部输入框（Enter 发送）、SSE 流式渲染、工具步骤着色（蓝=调用 / 绿=观测）。

## 必须读

- `SPEC.md`（迭代 6 增补 4）
- `agent/web.py`（`INDEX_HTML`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/web.py`（新 `INDEX_HTML`）
- 验收：`pytest -q` 全绿；浏览器打开页面可见对话式布局与流式气泡
