"""工具注册表：定义本地工具、导出 OpenAI function calling schema、按名分发。"""

from __future__ import annotations

from typing import Any

from .base import Tool
from .file_tools import EDIT_FILE, READ_FILE, WRITE_FILE
from .fs_tools import LIST_DIRECTORY, SEARCH_CONTENT
from .search_tools import WEB_SEARCH
from .shell_tools import EXECUTE_COMMAND
from .subagent_tools import DELEGATE_SUBAGENT, set_subagent_config
from .todo_tools import TODO_WRITE

TOOLS: list[Tool] = [
    READ_FILE,
    WRITE_FILE,
    EDIT_FILE,
    EXECUTE_COMMAND,
    LIST_DIRECTORY,
    SEARCH_CONTENT,
    WEB_SEARCH,
    TODO_WRITE,
    DELEGATE_SUBAGENT,
]

# chat 模式：只读工具集（不可编辑文件、执行命令、委派子代理）
READ_ONLY_TOOL_NAMES = {"read_file", "list_directory", "search_content", "web_search"}


def tool_schemas() -> list[dict[str, Any]]:
    """返回全部工具的 OpenAI function calling schema。"""
    return [t.to_schema() for t in TOOLS]


def tool_schemas_for(names: set[str] | None = None) -> list[dict[str, Any]]:
    """返回指定工具名的 schema（None 返回全部）。"""
    return [t.to_schema() for t in TOOLS if names is None or t.name in names]


def dispatch(name: str, arguments: dict[str, Any], workdir: str) -> str:
    """按工具名执行；未知工具返回错误观测。"""
    for tool in TOOLS:
        if tool.name == name:
            return tool.handler(arguments, workdir)
    return f"错误：未知工具 {name!r}"
