"""文件系统工具：list_directory / search_content。"""

from __future__ import annotations

from .base import Tool, resolve_path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".idea", ".vscode", "dist", "build"}
MAX_SEARCH_MATCHES = 200
MAX_FILE_BYTES = 1_000_000


def list_directory(arguments: dict, workdir: str) -> str:
    path = resolve_path(arguments.get("path", "."), workdir)
    if not path.is_dir():
        return f"错误：目录不存在 {path}"
    try:
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except OSError as exc:
        return f"错误：{exc}"
    if not entries:
        return "(空目录)"
    lines = []
    for entry in entries:
        if entry.is_dir():
            lines.append(f"[dir]  {entry.name}/")
        else:
            try:
                size = entry.stat().st_size
            except OSError:
                size = 0
            lines.append(f"[file] {entry.name} ({size} bytes)")
    return "\n".join(lines)


def search_content(arguments: dict, workdir: str) -> str:
    query = arguments["query"]
    root = resolve_path(arguments.get("path", "."), workdir)
    if not root.is_dir():
        return f"错误：目录不存在 {root}"
    matches: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if query in line:
                matches.append(f"{p.relative_to(root)}:{lineno}: {line.strip()}")
                if len(matches) >= MAX_SEARCH_MATCHES:
                    break
        if len(matches) >= MAX_SEARCH_MATCHES:
            break
    if not matches:
        return f"未找到包含 {query!r} 的内容"
    tail = "\n...（匹配过多，仅显示前 200 条）" if len(matches) >= MAX_SEARCH_MATCHES else ""
    return "\n".join(matches) + tail


LIST_DIRECTORY = Tool(
    name="list_directory",
    description="列出目录条目（名称 / 类型 / 大小）。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "目录路径，默认当前工作目录"},
        },
    },
    handler=list_directory,
)

SEARCH_CONTENT = Tool(
    name="search_content",
    description="在目录下递归搜索包含指定关键字的文本文件，返回 file:line:内容。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "要搜索的关键字（字面匹配）"},
            "path": {"type": "string", "description": "搜索根目录，默认当前工作目录"},
        },
        "required": ["query"],
    },
    handler=search_content,
)
