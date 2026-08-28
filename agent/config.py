"""配置加载：从环境变量或 .env 文件读取（自研 .env 解析，不引入第三方依赖）。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _project_root() -> Path:
    """返回项目根目录（agent 包的上一级，即 coding-agent/）。"""
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

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "缺少 DEEPSEEK_API_KEY：请在 .env 或环境变量中设置（参考 .env.example）"
            )
        return cls(
            api_key=api_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            max_iterations=int(os.environ.get("DEEPSEEK_MAX_ITERATIONS", "30")),
        )
