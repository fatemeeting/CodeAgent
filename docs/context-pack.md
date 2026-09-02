# context-pack.md — 当前阶段上下文包

> 当前阶段：**迭代 10 · 切片 10.2/10.3（按钮尺寸圆角 + 资源管理器文件操作）**

## 当前阶段目标

10.2：工作区选择与技能创建/管理界面的按钮统一胶囊圆角（999px）与尺寸（主按钮 padding 10px 18px / 15px，取消类同规格描边，禁用态中性色）。10.3：资源管理器支持文件操作——顶栏「＋ 文件/＋ 目录」内联命名输入；树节点 hover ✎ 重命名 / 🗑 两步确认删除；后端 `POST /fs-new`、`POST /fs-rename`、`DELETE /fs`（均带 is_relative_to 越界防护；目录仅空可删）；操作后刷新树并同步编辑器状态；修复 `saveFile` 用 basename 当路径的 bug（`currentFile` 存相对路径）。

## 必须读

- `SPEC.md` 第 32 节、`CHECKLIST.md` AX/AY 节
- `agent/web.py`：CSS（.btn/.btn-accent/.mgr-cancel/.tree-*）、`buildFileTree`/`renderTreeNode`/`loadTree`/`loadFile`/`saveFile`、`_handle_tree`/`_handle_file`/`_handle_save_file`、`do_POST`/`do_DELETE` 路由
- `tests/test_web.py`（端点测试模式）

## 不得读 / 不得改

- `.env`（真实凭据）
- `agent/loop.py`/`agent/llm.py`/`agent/skills.py`（无需改）

## 输出要求

- 产出：`agent/web.py`、`tests/test_web.py`
- 验收：`pytest -q` 全绿（约 158）；`node --check` + 无头垫片（新建/重命名/删除/编辑器同步）；真实服务冒烟（文件 CRUD + 越界防护）
