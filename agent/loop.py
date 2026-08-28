"""主循环：解析模型输出 → 执行工具 → 回填结果 → 循环，直到模型给出最终答复或达到迭代上限。"""

from __future__ import annotations

from typing import Any

from .config import Config
from .context import truncate_history
from .llm import LLMClient
from .parser import parse_response
from .tools import dispatch, tool_schemas

SYSTEM_PROMPT = (
    "你是一个编程智能体（coding agent）。用户会给你一个编程任务。"
    "你可以使用工具读写文件、执行命令、列目录、搜索文件内容，逐步完成任务。"
    "每次只执行一步，观察结果后再决定下一步。"
    "任务完成后直接给出简洁的最终总结，不要再调用工具。"
)

REFLECT_PROMPT = (
    "请自我检查：以上结果是否真正、完整地完成了用户的任务？"
    "如有遗漏或错误，请继续使用工具修正；若已完整正确，请直接回复一句确认。"
)

MAX_TOOL_TEXT = 4000  # 单条工具观测回填给模型前的截断上限，避免上下文膨胀


def _brief(text: Any, limit: int) -> str:
    """把文本压成单行简短摘要，超出限制用省略号截断。"""
    s = str(text)
    if len(s) <= limit:
        return s
    return s[:limit] + "…"


def _log_tool_call(step: int, name: str, arguments: dict[str, Any]) -> None:
    """打印工具调用（过程日志与最终答案都走 stdout，最终答案在最后一行）。"""
    print(f"[步骤 {step}] 调用工具 {name}：{_brief(arguments, 150)}")


def _log_observation(observation: str) -> None:
    collapsed = " | ".join(line.strip() for line in observation.splitlines() if line.strip())
    print(f"        ↳ {_brief(collapsed, 200)}")


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


def run_turn(
    client: LLMClient,
    config: Config,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    workdir: str,
) -> str:
    """在给定历史 messages 上执行一轮工具循环；原地更新 messages，返回最终文本。"""
    reflected = False
    pending_final: str | None = None
    for step in range(1, config.max_iterations + 1):
        messages[:] = truncate_history(messages, config.max_context_tokens)
        response = client.chat(messages, tools=tools)
        parsed = parse_response(response)

        # 终止条件 1：模型未请求工具，视为最终答复
        if not parsed.tool_calls:
            if config.reflect and not reflected:
                # 反思：首次给出答复后注入自检提示（仅一轮）
                reflected = True
                pending_final = parsed.content or ""
                messages.append({"role": "assistant", "content": pending_final})
                messages.append({"role": "user", "content": REFLECT_PROMPT})
                continue
            final = (pending_final or parsed.content) or "（模型未返回文本回复）"
            messages.append({"role": "assistant", "content": parsed.content or ""})
            return final

        # 模型要调用工具：反思发现问题，丢弃暂存的原答复
        pending_final = None
        messages.append(_assistant_message(parsed))
        for tc in parsed.tool_calls:
            _log_tool_call(step, tc.name, tc.arguments)
            try:
                observation = dispatch(tc.name, tc.arguments, workdir)
            except Exception as exc:  # noqa: BLE001 - 工具异常回填为观测，不中断循环
                observation = f"错误：工具 {tc.name} 执行异常：{exc}"
            if len(observation) > MAX_TOOL_TEXT:
                observation = observation[:MAX_TOOL_TEXT] + "\n...（观测过长已截断）"
            _log_observation(observation)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": observation})

    # 终止条件 2：达到最大迭代上限
    return f"（达到最大迭代次数 {config.max_iterations}，任务未完成）"


def run(
    config: Config,
    task: str,
    workdir: str = ".",
    client: LLMClient | None = None,
) -> str:
    """单次任务：构造 system + user(task)，跑一轮工具循环。可复用传入的 client。"""
    if client is None:
        client = LLMClient(config)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    return run_turn(client, config, messages, tool_schemas(), workdir)
