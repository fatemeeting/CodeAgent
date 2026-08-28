# gate-checklist.md — 阶段 0 放行清单

> 当前阶段：阶段 0（契约先行）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [ ] SPEC.md 覆盖：用户 / 目标 / 范围 / 非目标 / 技术约束 / 阶段划分
- [ ] CHECKLIST.md 每项可观察或可执行，含功能 / 工程 / 安全 / 体验 / 解释 / 退出
- [ ] AGENTS.md 含：目标 / 优先阅读 / 检查命令 / 禁止事项与安全边界
- [ ] `.gitignore` 忽略 `.env`、`__pycache__` 等
- [ ] `.env.example` 仅占位符，无真实 key
- [ ] `requirements.txt` 仅 `openai`

## 证据位置

- 文件本体：`SPEC.md`、`CHECKLIST.md`、`AGENTS.md`、`.gitignore`、`.env.example`、`requirements.txt`

## 退出决定

- 通过 → 进入阶段 1
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
