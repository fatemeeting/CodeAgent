"""命令行入口。"""

from __future__ import annotations

import argparse
from dataclasses import replace

from .config import Config
from .llm import LLMClient
from .loop import run
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = Config.from_env()
    if (
        args.model
        or args.max_iterations is not None
        or args.max_context_tokens is not None
        or args.reflect
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
        )
    if args.task is None:
        return repl(config, workdir=args.workdir or ".")
    client = LLMClient(config)
    result = run(config, args.task, workdir=args.workdir or ".", client=client)
    print(result)
    if args.suggest:
        print("\n你可能还想问：")
        print(suggest_followups(client, args.task))
    if args.usage:
        print(client.usage_summary_text())
    return 0
