"""模型输出解析：区分文本回复与工具调用（tool_calls），并对参数做防御式 JSON 解析。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    arguments_raw: str
    arguments: dict[str, Any]


@dataclass
class ParsedMessage:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)


def _parse_arguments(raw: Any) -> dict[str, Any]:
    """把模型的 arguments（JSON 字符串）解析为 dict；失败时返回含 _error 的占位。"""
    if isinstance(raw, dict):
        return raw
    raw = raw or ""
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        return {"_raw": raw, "_error": f"arguments 不是合法 JSON：{exc}"}
    return data if isinstance(data, dict) else {"_value": data}


def parse_response(response: Any) -> ParsedMessage:
    """把 OpenAI 兼容响应解析为 ParsedMessage（文本 + 工具调用列表）。"""
    choices = getattr(response, "choices", None)
    if not choices:
        return ParsedMessage(content="")
    message = getattr(choices[0], "message", None)
    if message is None:
        return ParsedMessage(content="")

    content = getattr(message, "content", None) or ""
    calls: list[ToolCall] = []
    for tc in getattr(message, "tool_calls", None) or []:
        fn = getattr(tc, "function", None)
        if fn is None:
            name, raw = "", ""
        else:
            name = getattr(fn, "name", "") or ""
            raw = getattr(fn, "arguments", "") or ""
        calls.append(
            ToolCall(
                id=getattr(tc, "id", "") or "",
                name=name,
                arguments_raw=raw,
                arguments=_parse_arguments(raw),
            )
        )
    return ParsedMessage(content=content, tool_calls=calls)
