"""工具注册表：定义本地工具、导出 OpenAI function calling schema、按名分发。"""

from __future__ import annotations

from typing import Any

from .base import Tool
from .file_tools import EDIT_FILE, READ_FILE, WRITE_FILE
from .fs_tools import LIST_DIRECTORY, SEARCH_CONTENT
from .search_tools import WEB_SEARCH
from .shell_tools import EXECUTE_COMMAND

TOOLS: list[Tool] = [
    READ_FILE,
    WRITE_FILE,
    EDIT_FILE,
    EXECUTE_COMMAND,
    LIST_DIRECTORY,
    SEARCH_CONTENT,
    WEB_SEARCH,
]


def tool_schemas() -> list[dict[str, Any]]:
    """返回全部工具的 OpenAI function calling schema。"""
    return [t.to_schema() for t in TOOLS]


def dispatch(name: str, arguments: dict[str, Any], workdir: str) -> str:
    """按工具名执行；未知工具返回错误观测。"""
    for tool in TOOLS:
        if tool.name == name:
            return tool.handler(arguments, workdir)
    return f"错误：未知工具 {name!r}"
