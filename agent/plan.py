"""任务规划（plan-first）：执行前先生成分步计划。"""

from __future__ import annotations

from .llm import LLMClient
from .parser import parse_response

PLAN_PROMPT = "先不要执行任何操作，只给出完成该任务的分步计划（3-6 步，每步一句，简洁直接）。"


def make_plan(client: LLMClient, task: str, feedback: str | None = None) -> str:
    """复用 client 再调一次模型（不带工具），返回分步计划文本。

    feedback 为用户对上一版计划的修改意见（/plan 两段式确认流程，迭代 10）。
    """
    user_text = f"任务：{task}\n\n{PLAN_PROMPT}"
    if feedback:
        user_text += f"\n\n用户对上一版计划的修改意见（必须采纳并体现在新计划中）：{feedback}"
    messages = [
        {"role": "system", "content": "你是编程任务的规划器，负责把任务拆解为清晰的可执行步骤。"},
        {"role": "user", "content": user_text},
    ]
    response = client.chat(messages)
    return parse_response(response).content or ""
