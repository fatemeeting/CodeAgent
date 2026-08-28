"""命令行入口。"""

from __future__ import annotations

import argparse
from dataclasses import replace

from .config import Config
from .llm import LLMClient
from .loop import run
from .plan import make_plan
from .repl import repl
from .suggest import suggest_followups


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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = Config.from_env()
    if (
        args.model
        or args.max_iterations is not None
        or args.max_context_tokens is not None
        or args.reflect
        or args.stream
        or args.confirm
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
        )
    if args.task is None:
        return repl(config, workdir=args.workdir or ".")
    client = LLMClient(config)
    task = args.task
    if args.plan:
        plan = make_plan(client, task)
        print("计划：")
        print(plan)
        print()
        task = f"{task}\n\n已制定的执行计划：\n{plan}\n请按计划逐步执行。"
    result = run(config, task, workdir=args.workdir or ".", client=client)
    if not config.stream:
        print(result)
    if args.suggest:
        print("\n你可能还想问：")
        print(suggest_followups(client, args.task))
    if args.usage:
        print(client.usage_summary_text())
    return 0
