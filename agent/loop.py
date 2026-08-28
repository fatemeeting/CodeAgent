"""主循环：解析模型输出 → 执行工具 → 回填结果 → 循环，直到模型给出最终答复或达到迭代上限。"""

from __future__ import annotations

from typing import Any

from .config import Config
from .llm import LLMClient
from .parser import parse_response
from .tools import dispatch, tool_schemas

SYSTEM_PROMPT = (
    "你是一个编程智能体（coding agent）。用户会给你一个编程任务。"
    "你可以使用工具读写文件、执行命令、列目录、搜索文件内容，逐步完成任务。"
    "每次只执行一步，观察结果后再决定下一步。"
    "任务完成后直接给出简洁的最终总结，不要再调用工具。"
)

MAX_TOOL_TEXT = 4000  # 单条工具观测回填给模型前的截断上限，避免上下文膨胀


def _assistant_message(parsed: Any) -> dict[str, Any]:
    """把解析结果重建为 OpenAI 兼容的 assistant 消息（含 tool_calls）。"""
    msg: dict[str, Any] = {"role": "assistant", "content": parsed.content or None}
    if parsed.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": tc.arguments_raw},
            }
            for tc in parsed.tool_calls
        ]
    return msg


def run(config: Config, task: str, workdir: str = ".") -> str:
    client = LLMClient(config)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    tools = tool_schemas()

    for _ in range(config.max_iterations):
        response = client.chat(messages, tools=tools)
        parsed = parse_response(response)

        # 终止条件 1：模型未请求工具，视为最终答复
        if not parsed.tool_calls:
            return parsed.content or "（模型未返回文本回复）"

        messages.append(_assistant_message(parsed))
        for tc in parsed.tool_calls:
            try:
                observation = dispatch(tc.name, tc.arguments, workdir)
            except Exception as exc:  # noqa: BLE001 - 工具异常回填为观测，不中断循环
                observation = f"错误：工具 {tc.name} 执行异常：{exc}"
            if len(observation) > MAX_TOOL_TEXT:
                observation = observation[:MAX_TOOL_TEXT] + "\n...（观测过长已截断）"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": observation})

    # 终止条件 2：达到最大迭代上限
    return f"（达到最大迭代次数 {config.max_iterations}，任务未完成）"
