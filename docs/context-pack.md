# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 8 · 切片 8.3（subagent 工具：delegate_subagent + 嵌套轨迹）**

## 当前阶段目标

新增 `delegate_subagent` 工具：独立子代理执行子任务（短预算 3 轮、不可再委托、goal/reflect 关闭、stdout 捕获静默、结果摘要回填 ≤400 字）；`run()` 增可选 `tools` 参数（子代理用排除自身后的工具集）；配置经 `set_subagent_config(config)` 注入（run 开始时设置，避免循环导入——handler 内惰性 import loop）；事件 `subagent_start{name,task} / subagent_end{ok,summary}`；前端「🤖 子代理」嵌套折叠块（运行态扫光 → ✓/✗ + 摘要）；并行由既有工具并行执行天然获得。

## 必须读

- `SPEC.md` 第 27 节切片 8.3
- `agent/loop.py`（`run`/`run_turn` 签名与事件点）、`agent/tools/__init__.py`、`agent/web.py`（`handleEvent`/`newTurnState`/`.tblk` CSS）
- `tests/test_tools.py`、`tests/test_loop.py`

## 不得读 / 不得改

- `.env`（真实凭据）

## 输出要求

- 产出：`agent/tools/subagent_tools.py`、`agent/tools/__init__.py`、`agent/loop.py`、`agent/web.py`、测试
- 验收：`pytest -q` 全绿（约 122）；`node --check`；DOM 垫片（子代理块/状态）；冒烟标记
