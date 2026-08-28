"""DeepSeek 客户端封装：OpenAI 兼容接口 + 自研错误处理（指数退避重试）。"""

from __future__ import annotations

import time
from typing import Any

from openai import OpenAI

from .config import Config


class LLMError(RuntimeError):
    """LLM 调用失败（重试耗尽后抛出）。"""


class LLMClient:
    def __init__(self, config: Config):
        self._config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_retries: int = 3,
    ) -> Any:
        """调用 chat.completions.create；失败时指数退避重试，耗尽抛 LLMError。"""
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                kwargs: dict[str, Any] = {
                    "model": self._config.model,
                    "messages": messages,
                }
                if tools:
                    kwargs["tools"] = tools
                return self._client.chat.completions.create(**kwargs)
            except Exception as exc:  # noqa: BLE001 - 统一捕获网络/API 错误后重试
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 8))
        raise LLMError(f"LLM 调用失败（已重试 {max_retries} 次）：{last_exc}") from last_exc
