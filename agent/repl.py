"""交互式多轮会话（REPL）：连续输入任务，跨轮保留对话历史。"""

from __future__ import annotations

from typing import Any

from .config import Config
from .llm import LLMClient
from .loop import SYSTEM_PROMPT, run_turn
from .tools import tool_schemas

HELP = "命令：/help 查看帮助 | /quit 退出 | /clear 清空历史 | /history 查看消息数"


def interpret(line: str) -> tuple[str, str | None]:
    """解析一行输入，返回 (action, payload)。action ∈ {empty, quit, help, clear, history, task}。"""
    s = line.strip()
    if not s:
        return ("empty", None)
    if s in ("/quit", "/exit"):
        return ("quit", None)
    if s == "/help":
        return ("help", None)
    if s == "/clear":
        return ("clear", None)
    if s == "/history":
        return ("history", None)
    return ("task", s)


def repl(config: Config, workdir: str = ".") -> int:
    client = LLMClient(config)
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    tools = tool_schemas()
    print("交互模式已启动。", HELP)
    while True:
        try:
            line = input(">> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        action, payload = interpret(line)
        if action == "empty":
            continue
        if action == "quit":
            print("再见。")
            break
        if action == "help":
            print(HELP)
            continue
        if action == "clear":
            messages[:] = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("已清空对话历史。")
            continue
        if action == "history":
            print(f"当前对话历史 {len(messages)} 条消息。")
            continue
        # action == "task"
        messages.append({"role": "user", "content": payload})
        result = run_turn(client, config, messages, tools, workdir)
        print(result)
    return 0
