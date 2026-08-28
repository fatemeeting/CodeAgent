"""命令工具：execute_command（本地 subprocess，带超时与输出截断）。"""

from __future__ import annotations

import os
import re
import subprocess

from .base import Tool

MAX_OUTPUT_CHARS = 20_000

DANGEROUS_PATTERNS = [
    r"\brm\b", r"\bdel\b", r"\brmdir\b", r"\brd\b",
    r"git\s+push", r"git\s+reset\s+--hard",
    r"format\s+[a-z]:", r"\bshutdown\b", r"\breboot\b", r"\btaskkill\b",
]


def is_dangerous(command: str) -> bool:
    """判断命令是否危险（删除 / 破坏性 git / 格式化 / 关机等）。"""
    return any(re.search(p, command, re.IGNORECASE) for p in DANGEROUS_PATTERNS)


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n...（输出过长，已截断，共 {len(s)} 字符）"


def execute_command(arguments: dict, workdir: str) -> str:
    command = arguments["command"]
    timeout = int(arguments.get("timeout", 60))
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=workdir,
            timeout=timeout,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    except subprocess.TimeoutExpired:
        return f"错误：命令超时（>{timeout} 秒）"
    except OSError as exc:
        return f"错误：命令执行失败 {exc}"
    parts = []
    if proc.stdout:
        parts.append(_truncate(proc.stdout.rstrip(), MAX_OUTPUT_CHARS))
    if proc.stderr:
        parts.append("[stderr]\n" + _truncate(proc.stderr.rstrip(), MAX_OUTPUT_CHARS))
    parts.append(f"[exit_code: {proc.returncode}]")
    return "\n".join(parts)


EXECUTE_COMMAND = Tool(
    name="execute_command",
    description="在工作目录内执行 shell 命令，返回 stdout / stderr / 退出码；命令须在超时内完成。",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的命令"},
            "timeout": {"type": "integer", "description": "超时秒数，默认 60"},
        },
        "required": ["command"],
    },
    handler=execute_command,
)
