# gate-checklist.md — 阶段 6 放行清单

> 当前阶段：阶段 6（提交物）。放行决定：通过 / 重试 / 降级 / 停止。

## 必过项

- [ ] `README.txt` 含仓库地址 / 如何运行 / 特色功能，≤1000 汉字
- [ ] 演示视频脚本 ≤2 分钟，含真实任务演示
- [ ] 推送到公开仓库，GitHub Actions CI 绿灯
- [ ] 提交历史完整（阶段 0–6，未改写）

## 证据位置

- README 与脚本：`README.txt`、`docs/video-script.md`
- CI 状态：GitHub Actions
- 提交历史：`git log`

## 退出决定

- 通过 → 项目完成（可打包提交 zip）
- 重试 → 补齐缺失项后复查
- 停止 → 记录原因
