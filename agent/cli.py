"""命令行入口。"""

from __future__ import annotations

import argparse
from dataclasses import replace

from .config import Config
from .loop import run
from .repl import repl


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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = Config.from_env()
    if (
        args.model
        or args.max_iterations is not None
        or args.max_context_tokens is not None
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
        )
    if args.task is None:
        return repl(config, workdir=args.workdir or ".")
    print(run(config, args.task, workdir=args.workdir or "."))
    return 0
