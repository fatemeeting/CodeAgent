"""任务清单工具：todo_write（模型维护全量清单，观测返回简短确认）。"""

from __future__ import annotations

from .base import Tool

MAX_TODOS = 30
CONTENT_CHARS = 100
VALID_STATUS = ("pending", "in_progress", "completed")


def _todo_write(arguments: dict, workdir: str) -> str:
    todos = arguments.get("todos")
    if not isinstance(todos, list):
        return "错误：todos 应为列表（每项含 id/content/status）"
    if len(todos) > MAX_TODOS:
        return f"错误：任务项过多（上限 {MAX_TODOS}）"
    cleaned = []
    for item in todos:
        if not isinstance(item, dict):
            return "错误：任务项应为对象 {id, content, status}"
        sid = str(item.get("id", "")).strip()
        content = str(item.get("content", "")).strip()[:CONTENT_CHARS]
        status = str(item.get("status", "pending")).strip()
        if status not in VALID_STATUS:
            status = "pending"
        if not content and not sid:
            continue
        cleaned.append({"id": sid or f"t{len(cleaned) + 1}", "content": content, "status": status})
    done = sum(1 for t in cleaned if t["status"] == "completed")
    prog = sum(1 for t in cleaned if t["status"] == "in_progress")
    return f"任务清单已更新：共 {len(cleaned)} 项（完成 {done} / 进行中 {prog} / 待办 {len(cleaned) - done - prog}）"


TODO_WRITE = Tool(
    name="todo_write",
    description=(
        "维护当前任务的待办清单（全量覆盖）：todos 为 [{id, content, status}]，"
        "status ∈ pending/in_progress/completed。复杂多步任务时用它记录与更新进度。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "任务清单全量快照",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "content": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                        },
                    },
                },
            },
        },
        "required": ["todos"],
    },
    handler=_todo_write,
)
