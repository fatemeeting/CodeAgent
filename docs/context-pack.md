# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 6 · 切片 6.1（极简 Web 终端）**

## 当前阶段目标

自写标准库 HTTP 服务（`http.server`，零新依赖）：`GET /` 返回表单页，`POST /run` 捕获 agent 全部输出并返回 JSON。入口 `python -m agent.web`。

## 必须读

- `SPEC.md`（迭代 6 范围）
- `agent/loop.py`（`run` 输出路径）
- `agent/config.py`（`Config.from_env`）
- `docs/context-snapshot.md`

## 不得读 / 不得改

- `.env`（真实凭据）
- 已放行代码（除非必要最小修改）

## 输出要求

- 产出：`agent/web.py`、`tests/test_web.py`
- 验收：`pytest -q` 全绿；本地起服务 POST 真实任务闭环
