"""交互式多轮会话（REPL）：连续输入任务，跨轮保留对话历史。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Config
from .context import load_history, save_history
from .llm import LLMClient
from .loop import SYSTEM_PROMPT, run_turn
from .tools import tool_schemas

HELP = "命令：/help 查看帮助 | /workdir [路径] 设置工作区 | /quit 退出 | /clear 清空历史 | /history 查看消息数 | /save [路径] | /load [路径] | /usage 查看用量"


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
    if s.startswith("/workdir"):
        return ("workdir", s[len("/workdir") :].strip() or None)
    if s.startswith("/save"):
        return ("save", s[len("/save") :].strip() or "history.json")
    if s.startswith("/load"):
        return ("load", s[len("/load") :].strip() or "history.json")
    if s == "/usage":
        return ("usage", None)
    return ("task", s)


def repl(config: Config, workdir: str = ".") -> int:
    client = LLMClient(config)
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    tools = tool_schemas()
    print("交互模式已启动。", HELP)
    while True:
        try:
            line = input(f"[{workdir}] >> ")
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
        if action == "workdir":
            if payload:
                p = Path(payload).expanduser().resolve()
                if not p.is_dir():
                    print(f"错误：目录不存在 {p}（请先创建）")
                    continue
                workdir = str(p)
                print(f"工作区已设置为：{workdir}")
            else:
                print(f"当前工作区：{workdir}")
            continue
        if action == "clear":
            messages[:] = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("已清空对话历史。")
            continue
        if action == "history":
            print(f"当前对话历史 {len(messages)} 条消息。")
            continue
        if action == "save":
            save_history(messages, payload)
            print(f"已保存对话历史到 {payload}（{len(messages)} 条消息）。")
            continue
        if action == "load":
            try:
                messages[:] = load_history(payload)
            except (FileNotFoundError, ValueError) as exc:
                print(f"加载失败：{exc}")
                continue
            print(f"已加载对话历史（{len(messages)} 条消息）。")
            continue
        if action == "usage":
            print(client.usage_summary_text())
            continue
        # action == "task"
        messages.append({"role": "user", "content": payload})
        result = run_turn(client, config, messages, tools, workdir)
        if not config.stream:
            print(result)
    return 0
