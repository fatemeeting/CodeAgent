# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 9 · 修复切片 3（任意位置输入 / 弹出浮层）**

## 当前阶段目标

用户反馈：希望**每一次输入 `/`**（任意位置，含句中）都弹出命令浮层。现逻辑只认输入开头。改 `buildCmdPop.render`：以光标前最后一个 `/` 起的「当前词」判定——`/skill` 词 → 技能列表；其它无空格词且匹配命令前缀 → 命令列表；选择命令/技能时只替换当前词（保留前置命令与后随任务），其余行为（☑ 多选、任务文本收起、Esc/↑↓/Enter）不变。

## 必须读

- `SPEC.md` 第 30 节、`CHECKLIST.md` AV 节
- `agent/web.py` 前端：`buildCmdPop`（render/命令项 onclick/技能项 act）、`lastSkillIndex`

## 不得读 / 不得改

- `.env`（真实凭据）
- 后端与 `parseCommand`/`sendTask`（无需改）

## 输出要求

- 产出：`agent/web.py` 前端；契约文件
- 验收：`pytest -q` 全绿（146）；`node --check` + 无头垫片（任意位置 `/`、词级替换、/skill 就地更新）；真实服务冒烟
