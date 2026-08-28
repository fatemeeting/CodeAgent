"""工具基础设施：Tool 定义、路径解析、按名分发。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# 处理函数签名：接收模型传入的参数与工作目录，返回字符串观测（回填给模型）。
Handler = Callable[[dict[str, Any], str], str]


def resolve_path(path: str, workdir: str) -> Path:
    """把相对路径解析到工作目录；绝对路径原样返回。"""
    p = Path(path)
    return p if p.is_absolute() else Path(workdir) / p


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Handler

    def to_schema(self) -> dict[str, Any]:
        """返回 OpenAI function calling 使用的工具 schema。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
