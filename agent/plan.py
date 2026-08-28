"""任务规划（plan-first）：执行前先生成分步计划。"""

from __future__ import annotations

from .llm import LLMClient
from .parser import parse_response

PLAN_PROMPT = "先不要执行任何操作，只给出完成该任务的分步计划（3-6 步，每步一句，简洁直接）。"


def make_plan(client: LLMClient, task: str) -> str:
    """复用 client 再调一次模型（不带工具），返回分步计划文本。"""
    messages = [
        {"role": "system", "content": "你是编程任务的规划器，负责把任务拆解为清晰的可执行步骤。"},
        {"role": "user", "content": f"任务：{task}\n\n{PLAN_PROMPT}"},
    ]
    response = client.chat(messages)
    return parse_response(response).content or ""
