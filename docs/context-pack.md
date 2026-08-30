# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 9 · 修复切片 2（命令组合与模式互斥）**

## 当前阶段目标

用户反馈：`/goal` 与 `/plan` 应互斥（只能选其一）；`/skill` 是独立维度，应与任一模式命令组合使用；现状是输入带 `/goal` 后就无法再 `/skill`。重写 `parseCommand` 为「多指令解析」：从输入任意位置提取 `/goal`、`/plan`、`/chat`（模式指令，互斥取先出现者）与 `/skill <names>`（可多个、names 累积去重，与模式独立），剩余文本为任务；`sendTask` 按模式优先级组装 URL（goal/plan→agent；chat→chat；仅 skill→agent）；技能浮层与技能栏点选支持在已有命令输入上追加/修改（取输入中**最后一个** `/skill` 指令操作）。后端零改动（`skill` 参数本就逗号分隔）。

## 必须读

- `SPEC.md` 第 30 节第 4 条（已补命令组合）、`CHECKLIST.md` AU 节
- `agent/web.py` 前端：`parseCommand`/`sendTask`/`buildCmdPop`/`parseSkillSelection`/`renderSkillRow`

## 不得读 / 不得改

- `.env`（真实凭据）
- 后端（零改动）

## 输出要求

- 产出：`agent/web.py` 前端；契约文件
- 验收：`pytest -q` 全绿（146）；`node --check` + 无头垫片（组合解析/互斥/追加/URL 组装/浮层）；真实服务冒烟
