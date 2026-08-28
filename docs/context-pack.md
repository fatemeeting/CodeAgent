# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 6 优化 · 完成（工作区先行 + 聊天式界面 + 原生文件夹选择器）**

## 本阶段已完成

- 切片 6.3 工作区先行：REPL `/workdir`（提示符显示）+ Web workdir 参数校验
- 切片 6.4 聊天式界面：气泡 + 流式 + 工具着色，模仿 DeepSeek Harness
- 切片 6.5 原生文件夹选择器：tkinter `askdirectory` + `/pick-workspace`

## 下一阶段（迭代 7）

- 候选：命令沙箱（真正隔离，替代模式匹配）/ 多 provider 切换
- 开工前先写：SPEC 增项 + CHECKLIST 增项 + 本 context-pack，再动代码

## 不得读 / 不得改

- `.env`（真实凭据）
- 已放行代码（除非必要最小修改）
