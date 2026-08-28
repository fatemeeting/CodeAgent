"""任务完成后的「猜你想问」：生成后续问题建议。"""

from __future__ import annotations

from .llm import LLMClient
from .parser import parse_response

SUGGEST_PROMPT = "基于上面的任务，列出 2-3 个用户接下来可能想问的相关问题，每行一个，简洁直接。"


def suggest_followups(client: LLMClient, task: str) -> str:
    """复用 client 再调一次模型（不带工具），返回后续问题建议文本。"""
    messages = [
        {"role": "system", "content": "你是编程助手，负责在任务完成后推荐后续问题。"},
        {"role": "user", "content": f"用户刚才的任务：{task}\n\n{SUGGEST_PROMPT}"},
    ]
    response = client.chat(messages)
    return parse_response(response).content or ""
