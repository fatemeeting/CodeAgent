"""配置加载：从环境变量或 .env 文件读取（自研 .env 解析，不引入第三方依赖）。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _project_root() -> Path:
    """返回项目根目录（agent 包的上一级）。"""
    return Path(__file__).resolve().parent.parent


def load_dotenv(path: str | Path | None = None) -> None:
    """极简 .env 解析器（替代 python-dotenv）。

    规则：
    - 支持 `KEY=VALUE` 与 `export KEY=VALUE`
    - 忽略空行与 `#` 注释
    - 仅当环境变量尚未设置时才写入（环境变量优先于 .env）
    """
    if path:
        candidates = [Path(path)]
    else:
        candidates = [Path.cwd() / ".env", _project_root() / ".env"]

    for p in candidates:
        if not p.is_file():
            continue
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


@dataclass(frozen=True)
class Config:
    """运行时配置（凭据仅保存在内存，不落盘）。"""

    api_key: str
    base_url: str
    model: str
    max_iterations: int
    max_context_tokens: int = 12000  # 上下文 token 预算（自研估算），超出则裁剪历史
    reflect: bool = False  # 最终答复前注入自检（reflection）
    stream: bool = False  # 流式输出最终答复
    confirm_dangerous: bool = False  # 危险命令执行前人工确认（human-in-the-loop）
    think: bool = False  # 开启思考：主模型切换 deepseek-reasoner（显式 DEEPSEEK_MODEL 优先）
    goal: bool = False  # 目标模式：长目标自动续跑（非「完成」开头不终止）

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "缺少 DEEPSEEK_API_KEY：请在 .env 或环境变量中设置（参考 .env.example）"
            )
        think = os.environ.get("DEEPSEEK_THINK", "").lower() in ("1", "true", "yes")
        model = os.environ.get("DEEPSEEK_MODEL") or (
            "deepseek-reasoner" if think else "deepseek-chat"
        )
        return cls(
            api_key=api_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model=model,
            max_iterations=int(os.environ.get("DEEPSEEK_MAX_ITERATIONS", "30")),
            max_context_tokens=int(os.environ.get("DEEPSEEK_MAX_CONTEXT_TOKENS", "12000")),
            reflect=os.environ.get("DEEPSEEK_REFLECT", "").lower() in ("1", "true", "yes"),
            stream=os.environ.get("DEEPSEEK_STREAM", "").lower() in ("1", "true", "yes"),
            confirm_dangerous=os.environ.get("DEEPSEEK_CONFIRM_DANGEROUS", "").lower()
            in ("1", "true", "yes"),
            think=think,
            goal=os.environ.get("DEEPSEEK_GOAL", "").lower() in ("1", "true", "yes"),
        )
