# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 7 · 切片 7.5 修复 3（DSH 对齐：工作区物理分层 + 中断轮次标记）**

## 当前阶段目标

① `SessionStore` 存储物理分层：`data/sessions/<ws-slug>/<id>.json`（slug = 归一化工作区安全名 + 8 位 md5），初始化时自动迁移旧平铺文件，读取兼容旧布局；② 前端重放末轮 trace 无 `turn_end` 时追加 `turn_end{interrupted:true}` 并渲染琥珀「上次中断」行；error 事件 severity=warn 渲染琥珀 warn 行（error 红 / warn 琥珀分级）。不做 zstd/SQLite/write-behind/fsync（超需求）。

## 必须读

- `SPEC.md` 第 26 节（本切片范围）
- `agent/sessions.py`（`_session_path`/`_write_session`/`create_session`/`__init__`）
- `agent/web.py`（`switchSession`/`handleEvent` 的 error 与 turn_end 分支/`.tblk.warn` CSS 缺失处）
- 参考（临时克隆）：`%TEMP%\dsh-harness\packages\session\session-persistence-jsonl\README.zh.md`（磁盘布局）

## 不得读 / 不得改

- `.env`（真实凭据）
- 其余端点与工具（只读）

## 输出要求

- 产出：`agent/sessions.py`、`agent/web.py`、`tests/test_sessions.py`
- 验收：`pytest -q` 全绿（约 98）；`node --check`；DOM 垫片（中断标记/warn 行）；冒烟标记
