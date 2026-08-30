# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 9 · 修复切片（/skill 命令与技能多选）**

## 当前阶段目标

用户反馈两处修复：① `/` 命令浮层只保留 `/skill`（移除 `/skills` 命令项），输入 `/skill` 后在同一浮层列出全部技能，点击累积多选（☑ 已选/再点取消，逗号分隔）；② 技能管理浮层点选不同技能时累积进 `/skill a,b` 而非互相覆盖；`/skill a,b [任务]` 发送时 URL 带 `&skill=a,b`（后端已支持逗号分隔，无需改）。技能管理（✎/🗑/只读）保留在顶栏「📚 技能」入口。

## 必须读

- `SPEC.md` 第 30 节第 4 条（已改）、`CHECKLIST.md` AT 节
- `agent/web.py` 前端：`CMD_ITEMS`/`parseCommand`/`buildCmdPop`/`sendTask`/`renderSkillRow`/`refreshSkillList`

## 不得读 / 不得改

- `.env`（真实凭据）
- 后端 `/skills` 端点与 `agent/skills.py`（无需改，回归保持）

## 输出要求

- 产出：`agent/web.py` 前端；契约文件
- 验收：`pytest -q` 全绿（146）；`node --check` + 无头垫片（弹层技能列表/多选累积/取消/多技能 URL/parseCommand）；真实服务冒烟
