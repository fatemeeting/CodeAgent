# context-snapshot.md — 已完成事实与未决问题

## 已完成事实（截至阶段 0）

- 需求来源已抽取：`requirement_doc/requierment_extracted.txt`（PDF 文本）
- 关键决策已确认：Python + DeepSeek API + 核心闭环 MVP
- 实施计划（8 阶段）已获用户确认

## 未完成 / 未决

- 阶段 0 契约文件正在产出（本快照所在时刻）
- 真实 `DEEPSEEK_API_KEY` 尚未就绪（阶段 1 冒烟前由用户注入环境变量）

## 下一阶段资料

- 阶段 1（骨架冒烟）需要：包结构、`config.py`、`llm.py`、最小 `loop.py`
- 冒烟验证需 `DEEPSEEK_API_KEY` 环境变量

## 不再重复讨论的决定

- 语言 = Python；模型 = DeepSeek（`deepseek-chat`）；范围 = 核心闭环 MVP
- 仅允许 `openai` 依赖；禁止一切 agent 框架
