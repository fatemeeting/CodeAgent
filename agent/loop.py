"""主循环：阶段 1 最小版本——发消息、打印回复（工具调用在阶段 3 接入）。"""

from __future__ import annotations

from .config import Config
from .llm import LLMClient

SYSTEM_PROMPT = "你是一个编程智能体（coding agent），帮助用户完成编程任务。"


def run(config: Config, task: str) -> str:
    client = LLMClient(config)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    response = client.chat(messages)
    content = response.choices[0].message.content or ""
    return content
