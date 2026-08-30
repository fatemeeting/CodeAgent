"""子代理工具：delegate_subagent（独立上下文的子任务执行，摘要回填）。

子代理约束：短预算（3 轮）、不可再委托（工具集排除自身）、goal/reflect 关闭、
stdout 捕获静默（仅返回结果摘要）。配置经 set_subagent_config 注入（run 开始时设置，
handler 内惰性 import loop 避免循环导入）。
"""

from __future__ import annotations

import contextlib
import io
from dataclasses import replace
from typing import Any

from .base import Tool
from ..config import Config

SUB_MAX_ITERATIONS = 3
SUMMARY_CHARS = 400

_CURRENT_CONFIG: Config | None = None


def set_subagent_config(config: Config | None) -> None:
    """注入当前主运行配置（run 开始时调用；子代理据此派生受限配置）。"""
    global _CURRENT_CONFIG
    _CURRENT_CONFIG = config


def _subagent_tools() -> list[dict[str, Any]]:
    """子代理工具集：排除 delegate_subagent（不可再委托）。"""
    from . import tool_schemas  # 惰性导入避免循环

    return [t for t in tool_schemas() if t["function"]["name"] != "delegate_subagent"]


def _delegate_subagent(arguments: dict, workdir: str) -> str:
    task = str(arguments.get("task") or "").strip()
    if not task:
        return "错误：缺少 task"
    cfg = _CURRENT_CONFIG
    if cfg is None:
        return "错误：子代理配置缺失（未在 run 中初始化）"
    from ..llm import LLMClient  # 惰性导入避免循环
    from ..loop import run

    sub_cfg = replace(
        cfg, max_iterations=SUB_MAX_ITERATIONS, goal=False, reflect=False, stream=False
    )
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            result = run(
                sub_cfg,
                task,
                workdir=workdir,
                client=LLMClient(sub_cfg),
                tools=_subagent_tools(),
            )
        summary = " ".join((result or "").split()).strip()[:SUMMARY_CHARS]
        return f"子代理完成：{summary}"
    except Exception as exc:  # noqa: BLE001 - 子代理异常回填观测
        return f"错误：子代理执行失败：{exc}"


DELEGATE_SUBAGENT = Tool(
    name="delegate_subagent",
    description=(
        "把独立子任务交给子代理在隔离上下文中执行，返回结果摘要。"
        "适用于可以独立完成的子问题（子代理不可再委托子代理）。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "子任务描述（完整自包含）"},
            "name": {"type": "string", "description": "子任务展示名（可选）"},
        },
        "required": ["task"],
    },
    handler=_delegate_subagent,
)
