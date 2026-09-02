"""命令行入口。"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from .config import Config
from .llm import LLMClient
from .loop import run
from .plan import make_plan
from .repl import repl
from .suggest import suggest_followups


def _harden_stdio() -> None:
    """stdout/stderr 编码容错：管道重定向下遇 GBK 不可编码字符（如 ↳）不再崩溃。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass  # 旧 Python / 不支持 reconfigure 时保持原行为


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent",
        description="编程智能体：通过大模型自主读写文件、执行命令，完成编程任务",
    )
    parser.add_argument("task", nargs="?", help="交给 agent 的编程任务（省略则进入交互模式）")
    parser.add_argument("--model", help="覆盖模型名（默认 DEEPSEEK_MODEL / deepseek-chat）")
    parser.add_argument("--max-iterations", type=int, help="工具循环最大迭代次数")
    parser.add_argument("--workdir", help="工具执行的工作目录（默认当前目录）")
    parser.add_argument("--max-context-tokens", type=int, help="上下文 token 预算（超出则裁剪历史）")
    parser.add_argument("--usage", action="store_true", help="运行后输出 token 用量与估算费用")
    parser.add_argument("--reflect", action="store_true", help="最终答复前注入自检（reflection）")
    parser.add_argument("--suggest", action="store_true", help="任务完成后推荐后续问题（猜你想问）")
    parser.add_argument("--stream", action="store_true", help="最终答复流式输出")
    parser.add_argument("--plan", action="store_true", help="执行前先生成分步计划")
    parser.add_argument("--confirm", action="store_true", help="危险命令执行前人工确认")
    parser.add_argument("--goal", action="store_true", help="目标模式：长目标自动续跑，受阻或连续无进展才终止")
    parser.add_argument("--skill", action="append", help="显式装载技能（可重复，按 name）")
    parser.add_argument("--list-skills", action="store_true", help="列出可用技能并退出（无需 API key）")
    return parser


def main(argv: list[str] | None = None) -> int:
    _harden_stdio()
    args = build_parser().parse_args(argv)
    if args.list_skills:
        from .skills import load_skills, skill_summary

        for s in skill_summary(load_skills(args.workdir or ".")):
            source = {"builtin": "内置", "env": "SKILLS_DIR", "workspace": "工作区"}.get(s["source"], s["source"])
            print(f"{s['name']}（{source}）— {s['description']}")
        return 0
    config = Config.from_env()
    if (
        args.model
        or args.max_iterations is not None
        or args.max_context_tokens is not None
        or args.reflect
        or args.stream
        or args.confirm
        or args.goal
    ):
        config = replace(
            config,
            model=args.model or config.model,
            max_iterations=(
                args.max_iterations if args.max_iterations is not None else config.max_iterations
            ),
            max_context_tokens=(
                args.max_context_tokens
                if args.max_context_tokens is not None
                else config.max_context_tokens
            ),
            reflect=args.reflect or config.reflect,
            stream=args.stream or config.stream,
            confirm_dangerous=args.confirm or config.confirm_dangerous,
            goal=args.goal or config.goal,
        )
    if args.task is None:
        return repl(config, workdir=args.workdir or ".")
    client = LLMClient(config)
    task = args.task
    if args.plan:
        plan = make_plan(client, task)
        while True:
            print("计划：")
            print(plan)
            print()
            try:
                answer = input(
                    "是否按此计划执行？(y=执行 / n=取消 / 直接输入修改意见重新生成) "
                )
            except (EOFError, KeyboardInterrupt):
                print("\n未确认计划，已取消执行。")
                return 0
            a = answer.encode("utf-8", errors="replace").decode("utf-8").strip()  # 净化孤立代理字符（管道编码错配）
            if a.lower() in ("y", "yes", "是"):
                break
            if a.lower() in ("n", "no", "否"):
                print("已取消执行。")
                return 0
            plan = make_plan(client, task, feedback=a)  # 带修改意见重新生成
        task = f"{task}\n\n已确认的执行计划：\n{plan}\n请严格按计划逐步执行。"
    skills = None
    if args.skill:
        from .skills import load_skills

        skills_map = load_skills(args.workdir or ".")
        skills = [skills_map[n] for n in args.skill if n in skills_map]
    result = run(config, task, workdir=args.workdir or ".", client=client, skills=skills)
    if not config.stream:
        print(result)
    if args.suggest:
        print("\n你可能还想问：")
        print(suggest_followups(client, args.task))
    if args.usage:
        print(client.usage_summary_text())
    return 0
