"""主循环：解析模型输出 → 执行工具 → 回填结果 → 循环，直到模型给出最终答复或达到迭代上限。"""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from .config import Config
from .context import truncate_history
from .llm import LLMClient
from .parser import parse_response
from .tools import dispatch, tool_schemas
from .tools.shell_tools import is_dangerous

SYSTEM_PROMPT = (
    "你是一个编程智能体（coding agent）。用户会给你一个编程任务。"
    "你可以使用工具读写文件、执行命令、列目录、搜索文件内容，逐步完成任务。"
    "每次只执行一步，观察结果后再决定下一步。"
    "任务完成后直接给出简洁的最终总结，不要再调用工具。"
    "重要规则：写入代码文件的内容必须是纯代码，符合该语言的代码规范、可直接运行；"
    "严禁把 Markdown 标记（如 ``` 围栏、** 加粗、# 标题）写进代码文件。"
    "最终总结可以用 Markdown 排版，但文件内容必须纯净。"
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


def _event(kind: str, **fields: Any) -> dict[str, Any]:
    """构造轨迹事件：统一带 text 兜底字段（旧前端只读 text，非正文事件不污染对话）。"""
    fields.setdefault("text", "")
    return {"type": kind, **fields}


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


def _safe_dispatch(name: str, arguments: dict[str, Any], workdir: str) -> str:
    try:
        return dispatch(name, arguments, workdir)
    except Exception as exc:  # noqa: BLE001 - 工具异常回填为观测，不中断循环
        return f"错误：工具 {name} 执行异常：{exc}"


def _timed_dispatch(name: str, arguments: dict[str, Any], workdir: str) -> tuple[str, int]:
    """执行单个工具并计时，返回 (观测, 耗时毫秒)。"""
    t0 = time.time()
    obs = _safe_dispatch(name, arguments, workdir)
    return obs, int((time.time() - t0) * 1000)


def _execute_tool_calls(tool_calls: list[Any], workdir: str) -> list[tuple[str, int]]:
    """并行执行多个工具调用（API 契约：同批 tool_calls 相互独立）；返回按序 (观测, 耗时)。"""
    if len(tool_calls) == 1:
        return [_timed_dispatch(tool_calls[0].name, tool_calls[0].arguments, workdir)]
    with ThreadPoolExecutor(max_workers=len(tool_calls)) as pool:
        futures = [
            pool.submit(_timed_dispatch, tc.name, tc.arguments, workdir) for tc in tool_calls
        ]
        return [f.result() for f in futures]


def _confirm_dangerous(command: str) -> bool:
    """人工确认危险命令；非交互（EOF）视为拒绝。"""
    try:
        answer = input(f"⚠️ 检测到危险命令：{command}\n是否执行？(y/N) ")
    except (EOFError, KeyboardInterrupt):
        return False
    return answer.strip().lower() == "y"


def run_turn(
    client: LLMClient,
    config: Config,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    workdir: str,
    emit: Callable[[dict[str, Any]], None] | None = None,
) -> str:
    """在给定历史 messages 上执行一轮工具循环；原地更新 messages，返回最终文本。

    emit 为轨迹事件回调（Web 事件流用）；为 None 时保持 CLI 的 stdout 打印行为。
    """
    reflected = False
    pending_final: str | None = None
    for step in range(1, config.max_iterations + 1):
        messages[:] = truncate_history(messages, config.max_context_tokens)
        think_started = False

        def on_reasoning(text: str) -> None:
            nonlocal think_started
            if not think_started:
                emit(_event("think_start"))
                think_started = True
            emit(_event("think_delta", text=text))

        def on_content(text: str) -> None:
            emit(_event("content_delta", text=text))

        def on_retry(attempt: int, max_retries: int, exc: Exception) -> None:
            if emit:
                emit(_event("retry", attempt=attempt, max=max_retries, message=str(exc)))

        if config.stream:
            response = client.chat_stream(
                messages,
                tools=tools,
                on_content=on_content if emit else None,
                on_reasoning=on_reasoning if emit else None,
                on_retry=on_retry if emit else None,
            )
        else:
            response = client.chat(messages, tools=tools, on_retry=on_retry if emit else None)
        parsed = parse_response(response)

        if emit:
            reasoning = getattr(response, "reasoning", None)
            if isinstance(reasoning, str) and reasoning and not think_started:
                emit(_event("think_start"))
                emit(_event("think_delta", text=reasoning))
            if think_started or (isinstance(reasoning, str) and reasoning):
                emit(_event("think_end"))
            if not config.stream and not parsed.tool_calls and parsed.content:
                emit(_event("content_delta", text=parsed.content))
            emit(_event("round_end", has_tools=bool(parsed.tool_calls)))

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
            if emit:
                emit(_event("tool_call", step=step, name=tc.name, parameter=tc.arguments_raw or ""))
            else:
                _log_tool_call(step, tc.name, tc.arguments)

        # human-in-the-loop：危险命令执行前人工确认（拒绝则不执行）
        refused: dict[int, str] = {}
        if config.confirm_dangerous:
            for i, tc in enumerate(parsed.tool_calls):
                command = str(tc.arguments.get("command", ""))
                if tc.name == "execute_command" and is_dangerous(command):
                    if not _confirm_dangerous(command):
                        refused[i] = f"用户取消了危险命令：{command}"

        # 参数 JSON 解析失败：不执行，事件化并回填错误观测供模型修正
        bad_args: dict[int, str] = {}
        for i, tc in enumerate(parsed.tool_calls):
            err = tc.arguments.get("_error") if isinstance(tc.arguments, dict) else None
            if err:
                bad_args[i] = f"错误：工具 {tc.name} 参数解析失败：{err}"
                if emit:
                    emit(_event(
                        "error",
                        severity="error",
                        retryable=True,
                        message=f"工具 {tc.name} 参数解析失败：{err}",
                    ))

        executable_indices = [
            i for i in range(len(parsed.tool_calls)) if i not in refused and i not in bad_args
        ]
        executable_calls = [parsed.tool_calls[i] for i in executable_indices]
        results = _execute_tool_calls(executable_calls, workdir) if executable_calls else []
        observations: list[str] = [""] * len(parsed.tool_calls)
        for i, (obs, _ms) in zip(executable_indices, results):
            observations[i] = obs
        durations = {i: ms for i, (_obs, ms) in zip(executable_indices, results)}
        for i, obs in refused.items():
            observations[i] = obs
        for i, obs in bad_args.items():
            observations[i] = obs

        for i, (tc, observation) in enumerate(zip(parsed.tool_calls, observations)):
            full_obs = observation  # 轨迹用完整观测（不截断）
            if len(observation) > MAX_TOOL_TEXT:
                observation = observation[:MAX_TOOL_TEXT] + "\n...（观测过长已截断）"
            if emit:
                exit_code = None
                if tc.name == "execute_command":
                    m = re.search(r"\[exit_code: (-?\d+)\]", full_obs)
                    if m:
                        exit_code = int(m.group(1))
                emit(_event(
                    "tool_result",
                    step=step,
                    name=tc.name,
                    ok=not full_obs.startswith("错误"),
                    output=full_obs,
                    duration_ms=durations.get(i, 0),
                    exit_code=exit_code,
                ))
            else:
                _log_observation(observation)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": observation})

    # 终止条件 2：达到最大迭代上限
    final = f"（达到最大迭代次数 {config.max_iterations}，任务未完成）"
    if emit:
        emit(_event("error", severity="warn", message=final, text=final))
    elif config.stream:
        print(final)  # 流式模式下该消息非模型输出，需自行打印
    return final


def run(
    config: Config,
    task: str,
    workdir: str = ".",
    client: LLMClient | None = None,
    emit: Callable[[dict[str, Any]], None] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> str:
    """单次任务：构造 system + user(task)，跑一轮工具循环。可复用传入的 client。

    emit 为轨迹事件回调（Web 用）；为 None 时保持 CLI 打印行为。
    history 为前置对话（[{"role": "user"/"assistant", "content": ...}]），
    供 Web 同一会话内多轮上下文互通（参考 DSH 多轮设计）。
    """
    if client is None:
        client = LLMClient(config)
    if emit:
        emit(_event("turn_start", task=task))
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": task})
    try:
        return run_turn(client, config, messages, tool_schemas(), workdir, emit)
    finally:
        if emit:
            usage: dict[str, Any] = {}
            getter = getattr(client, "usage_summary", None)
            if callable(getter):
                try:
                    raw = getter()
                    if isinstance(raw, dict):
                        usage = {str(k): int(v) for k, v in raw.items() if isinstance(v, int)}
                except Exception:  # noqa: BLE001 - 统计失败不影响主流程
                    usage = {}
            emit(_event("turn_end", usage=usage))
