"""文件工具：read_file / write_file / edit_file。"""

from __future__ import annotations

from .base import Tool, resolve_path

MAX_READ_BYTES = 100_000


def read_file(arguments: dict, workdir: str) -> str:
    path = resolve_path(arguments["path"], workdir)
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return f"错误：文件不存在 {path}"
    except IsADirectoryError:
        return f"错误：{path} 是目录，请改用 list_directory"
    except OSError as exc:
        return f"错误：读取失败 {exc}"
    truncated = len(data) > MAX_READ_BYTES
    if truncated:
        data = data[:MAX_READ_BYTES]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return f"错误：{path} 不是 UTF-8 文本（可能是二进制文件）"
    if truncated:
        text += f"\n...（文件过大，已截断，仅显示前 {MAX_READ_BYTES} 字节）"
    return text


def write_file(arguments: dict, workdir: str) -> str:
    path = resolve_path(arguments["path"], workdir)
    content = arguments["content"]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return f"错误：写入失败 {exc}"
    return f"已写入 {path}（{len(content.encode('utf-8'))} 字节）"


def edit_file(arguments: dict, workdir: str) -> str:
    path = resolve_path(arguments["path"], workdir)
    old = arguments["old_string"]
    new = arguments["new_string"]
    replace_all = bool(arguments.get("replace_all", False))
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"错误：文件不存在 {path}"
    except UnicodeDecodeError:
        return f"错误：{path} 不是 UTF-8 文本"
    count = text.count(old)
    if count == 0:
        return f"错误：未找到要替换的片段 {old!r}"
    if count > 1 and not replace_all:
        return f"错误：匹配到 {count} 处，请提供更精确片段或设 replace_all=true"
    text = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        return f"错误：写入失败 {exc}"
    return f"已替换 {count if replace_all else 1} 处"


READ_FILE = Tool(
    name="read_file",
    description="读取指定文件的 UTF-8 文本内容；大文件会截断。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径（相对工作目录或绝对路径）"},
        },
        "required": ["path"],
    },
    handler=read_file,
)

WRITE_FILE = Tool(
    name="write_file",
    description="创建或覆盖文件；父目录不存在时自动创建。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "要写入的完整内容"},
        },
        "required": ["path", "content"],
    },
    handler=write_file,
)

EDIT_FILE = Tool(
    name="edit_file",
    description="对文件做最小替换：把 old_string 替换为 new_string（默认仅替换一处）。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "old_string": {"type": "string", "description": "要替换的原文片段"},
            "new_string": {"type": "string", "description": "替换后的内容"},
            "replace_all": {"type": "boolean", "description": "是否替换全部匹配，默认 false"},
        },
        "required": ["path", "old_string", "new_string"],
    },
    handler=edit_file,
)
