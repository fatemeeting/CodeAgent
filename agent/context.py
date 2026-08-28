"""上下文管理：对话历史维护与 token 预算截断（自研估算，不引入 tokenizer 依赖）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：ASCII 约 4 字符 / token，其它（含中文）约 1 字符 / token。"""
    if not text:
        return 0
    ascii_count = sum(1 for c in text if ord(c) < 128)
    other_count = len(text) - ascii_count
    return max(1, ascii_count // 4 + other_count)


def _message_text(message: dict[str, Any]) -> str:
    """提取一条消息的文本（含工具调用参数），用于估算 token。"""
    parts: list[str] = []
    content = message.get("content")
    if content:
        parts.append(str(content))
    for tc in message.get("tool_calls") or []:
        fn = tc.get("function") if isinstance(tc, dict) else None
        if fn and fn.get("arguments"):
            parts.append(str(fn["arguments"]))
    return "\n".join(parts)


def truncate_history(messages: list[dict[str, Any]], max_tokens: int) -> list[dict[str, Any]]:
    """在 token 预算内裁剪历史。

    - 始终保留 system 与首条 user（任务）
    - 从尾部尽量保留最近消息，超出预算的部分丢弃
    - 丢弃尾部开头的孤儿 tool 消息（其 assistant 父消息已被裁掉），
      以保证 OpenAI tool calling 的配对约束
    """
    if not messages:
        return []

    head: list[dict[str, Any]] = []
    body = messages

    if messages[0].get("role") == "system":
        head.append(messages[0])
        body = messages[1:]

    for i, m in enumerate(body):
        if m.get("role") == "user":
            head.append(m)
            body = body[i + 1 :]
            break

    def cost(m: dict[str, Any]) -> int:
        return estimate_tokens(_message_text(m))

    used = sum(cost(m) for m in head)

    tail: list[dict[str, Any]] = []
    for m in reversed(body):
        c = cost(m)
        if used + c > max_tokens:
            break
        tail.append(m)
        used += c
    tail.reverse()

    while tail and tail[0].get("role") == "tool":
        tail.pop(0)

    return head + tail


def save_history(messages: list[dict[str, Any]], path: str) -> None:
    """把消息历史序列化为 JSON 保存到文件（仅消息，不含凭据）。"""
    Path(path).write_text(
        json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_history(path: str) -> list[dict[str, Any]]:
    """从 JSON 文件加载消息历史。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"历史文件格式错误（应为列表）：{path}")
    return data
