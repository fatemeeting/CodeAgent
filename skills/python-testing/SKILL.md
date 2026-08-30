---
name: python-testing
description: Python 单元测试规范（pytest）：先测后写、AAA 结构、覆盖边界与回归，测试全绿再收尾
keywords: pytest, 单测, 测试, unittest, 用例, 回归, coverage, mock
modes: agent
---
# Python 单元测试规范（pytest）

## 原则
1. 功能与测试同一切片交付：改代码必补/改测试；优先测试先行（先写失败用例再实现）。
2. 用 pytest 语法（`def test_*`、`assert`、`pytest.raises`），不引入 pytest 之外的新依赖。
3. 用例结构 AAA：Arrange（准备）/ Act（执行）/ Assert（断言）；一个用例只验一件事，命名描述行为。

## 必须覆盖
- 主路径：正常输入 → 期望输出。
- 边界：空输入、单元素、超长、非法类型、None。
- 错误路径：异常类型与消息（`pytest.raises(ValueError, match=...)`）。
- 回归：修复 bug 前先写复现该 bug 的失败用例，修复后保持通过。

## 隔离与替身
- 外部 API / LLM / 网络一律 `unittest.mock` 替换（本仓库约定：mock LLM 免 key）。
- 临时文件用 pytest 内置 `tmp_path`，不写死路径、不落仓库；测试不得依赖执行顺序与共享状态。

## 收尾检查
- `python -m pytest -q` 全绿再收尾；失败项定位到具体用例，只修对应切片，不扩大范围。
- 新增行为必须有对应用例；删除/改名的旧用例同步清理，不留孤儿测试。
