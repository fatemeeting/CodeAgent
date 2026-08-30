---
name: web-frontend
description: 前端开发规范（HTML/CSS/JS 零依赖）：textContent 防 XSS、CSS 变量、布局稳定、SSE 断线防护
keywords: 前端, web, html, css, javascript, js, ui, 界面, 样式, sse
modes: agent
---
# 前端开发规范（零依赖，标准库后端内联页面）

## 安全
- 动态文本一律 `textContent` 赋值；禁止把未转义内容拼进 innerHTML。
- 富文本用迷你 Markdown 渲染器（textContent 构建节点）而非直接 innerHTML；脚本禁用 eval / new Function。

## 结构与样式
- 颜色 / 圆角走 CSS 变量（--bg / --surface / --text / --accent / --border 等），不散写色值；状态色（成功 / 错误）统一。
- 三栏布局：显式高度链（height:0 + flex:1）、min-height/min-width:0、输入条 flex-shrink:0；弹层卡片 max-height 92vh 可滚动；窄屏栏宽 ≤ 38vw。
- 新面板复用现有弹层（#modal / .mgr-card），不另起一套骨架。

## 行为
- 流式 UI 用 SSE 且以 [DONE] 收尾；onerror 必须 close() 防止 EventSource 自动重连导致服务端重复运行。
- 交互按钮加 title；破坏性操作两步确认；状态用图标 + 颜色双重表达。
- 命令浮层（/ 开头）支持 ↑↓/Enter/Esc 键盘导航与点击插入。

## 验收
- 改前端后：提取内联脚本 `node --check` 语法通过；无头 DOM 垫片冒烟关键路径（命令解析、事件块渲染、面板 CRUD）。
- 旧功能回归：空状态不报错、Console 无红色错误、窄屏可读。
