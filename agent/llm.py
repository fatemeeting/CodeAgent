"""DeepSeek 客户端封装：OpenAI 兼容接口 + 自研错误处理（指数退避重试）。"""

from __future__ import annotations

import time
from typing import Any

from openai import OpenAI

from .config import Config


class LLMError(RuntimeError):
    """LLM 调用失败（重试耗尽后抛出）。"""


# DeepSeek V3 估算价格（USD / 百万 token），仅用于粗略费用统计
INPUT_PRICE_PER_M = 0.27
OUTPUT_PRICE_PER_M = 1.10


class LLMClient:
    def __init__(self, config: Config):
        self._config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        self.prompt_tokens = 0
        self.completion_tokens = 0

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
                response = self._client.chat.completions.create(**kwargs)
                self._record_usage(response)
                return response
            except Exception as exc:  # noqa: BLE001 - 统一捕获网络/API 错误后重试
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 8))
        raise LLMError(f"LLM 调用失败（已重试 {max_retries} 次）：{last_exc}") from last_exc

    def _record_usage(self, response: Any) -> None:
        """从响应累计 token 用量（mock 响应无 usage 时跳过）。"""
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        prompt = getattr(usage, "prompt_tokens", 0)
        completion = getattr(usage, "completion_tokens", 0)
        if isinstance(prompt, int):
            self.prompt_tokens += prompt
        if isinstance(completion, int):
            self.completion_tokens += completion

    def usage_summary(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
        }

    def usage_summary_text(self) -> str:
        u = self.usage_summary()
        cost = (
            u["prompt_tokens"] / 1_000_000 * INPUT_PRICE_PER_M
            + u["completion_tokens"] / 1_000_000 * OUTPUT_PRICE_PER_M
        )
        return (
            f"token 用量：prompt {u['prompt_tokens']} / completion {u['completion_tokens']}"
            f" / 总计 {u['total_tokens']}（估算费用约 ${cost:.4f}）"
        )
