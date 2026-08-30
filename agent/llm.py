"""DeepSeek 客户端封装：OpenAI 兼容接口 + 自研错误处理（指数退避重试）。"""

from __future__ import annotations

import time
from types import SimpleNamespace
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
        on_retry=None,
    ) -> Any:
        """调用 chat.completions.create；失败时指数退避重试，耗尽抛 LLMError。

        on_retry(attempt, max_retries, exc)：每次重试前的回调（attempt 从 1 起）。
        """
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
                self._attach_reasoning(response)
                return response
            except Exception as exc:  # noqa: BLE001 - 统一捕获网络/API 错误后重试
                last_exc = exc
                if attempt < max_retries - 1:
                    if on_retry:
                        try:
                            on_retry(attempt + 1, max_retries, exc)
                        except Exception:  # noqa: BLE001 - 回调异常不影响重试
                            pass
                    time.sleep(min(2 ** attempt, 8))
        raise LLMError(f"LLM 调用失败（已重试 {max_retries} 次）：{last_exc}") from last_exc

    @staticmethod
    def _attach_reasoning(response: Any) -> None:
        """把 reasoning_content（deepseek-reasoner 思考内容）挂载为 response.reasoning。"""
        try:
            reasoning = getattr(response.choices[0].message, "reasoning_content", None)
        except Exception:  # noqa: BLE001 - mock / 异常结构容错
            return
        if isinstance(reasoning, str) and reasoning:
            try:
                response.reasoning = reasoning
            except Exception:  # noqa: BLE001 - 只读对象则放弃挂载
                pass

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

    def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_retries: int = 3,
        on_content=None,
        on_reasoning=None,
        on_retry=None,
    ) -> Any:
        """流式调用：逐 token 打印（或经回调转发）内容，并重建 tool_calls 返回等价响应。

        on_content(text)：内容增量回调（设置后不再打印到 stdout）；
        on_reasoning(text)：deepseek-reasoner 思考增量回调；
        on_retry(attempt, max_retries, exc)：每次重试前的回调。
        """
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                return self._chat_stream_once(messages, tools, on_content, on_reasoning)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < max_retries - 1:
                    if on_retry:
                        try:
                            on_retry(attempt + 1, max_retries, exc)
                        except Exception:  # noqa: BLE001 - 回调异常不影响重试
                            pass
                    time.sleep(min(2 ** attempt, 8))
        raise LLMError(f"LLM 流式调用失败（已重试 {max_retries} 次）：{last_exc}") from last_exc

    def _chat_stream_once(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        on_content=None,
        on_reasoning=None,
    ) -> Any:
        kwargs: dict[str, Any] = {"model": self._config.model, "messages": messages, "stream": True}
        if tools:
            kwargs["tools"] = tools
        stream = self._client.chat.completions.create(**kwargs)

        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        tool_buf: dict[int, dict[str, str]] = {}
        usage: Any = None
        for chunk in stream:
            if getattr(chunk, "usage", None) is not None:
                usage = chunk.usage
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            if delta is None:
                continue
            reasoning = getattr(delta, "reasoning_content", None)
            if isinstance(reasoning, str) and reasoning:
                reasoning_parts.append(reasoning)
                if on_reasoning:
                    on_reasoning(reasoning)
            content = getattr(delta, "content", None)
            if content:
                content_parts.append(content)
                if on_content:
                    on_content(content)
                else:
                    print(content, end="", flush=True)
            for tc in getattr(delta, "tool_calls", None) or []:
                idx = getattr(tc, "index", 0)
                buf = tool_buf.setdefault(idx, {"id": "", "name": "", "arguments": ""})
                if getattr(tc, "id", None):
                    buf["id"] = tc.id
                fn = getattr(tc, "function", None)
                if fn is not None:
                    if getattr(fn, "name", None):
                        buf["name"] = fn.name
                    if getattr(fn, "arguments", None):
                        buf["arguments"] += fn.arguments

        if content_parts and not on_content:
            print()  # 流式内容结束后补换行（CLI 打印模式）
        response = self._build_streamed_response("".join(content_parts), tool_buf, usage)
        reasoning = "".join(reasoning_parts)
        if reasoning:
            response.reasoning = reasoning
        self._record_usage(response)
        return response

    def _build_streamed_response(
        self, content: str, tool_buf: dict[int, dict[str, str]], usage: Any
    ) -> Any:
        tool_calls = []
        for idx in sorted(tool_buf):
            b = tool_buf[idx]
            fn = SimpleNamespace(name=b["name"], arguments=b["arguments"])
            tool_calls.append(SimpleNamespace(id=b["id"], function=fn))
        msg = SimpleNamespace(content=content, tool_calls=tool_calls or None)
        choice = SimpleNamespace(message=msg)
        return SimpleNamespace(choices=[choice], usage=usage)
