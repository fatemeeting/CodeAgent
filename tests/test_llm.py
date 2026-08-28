"""llm.py 单元测试：重试与错误处理（mock OpenAI 客户端，不发起真实请求）。"""

from unittest import mock

import pytest

from agent.config import Config
from agent.llm import LLMClient, LLMError


def _config() -> Config:
    return Config(
        api_key="test-key",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=30,
    )


def test_chat_returns_content():
    client = LLMClient(_config())
    fake_resp = mock.Mock(choices=[mock.Mock(message=mock.Mock(content="hi"))])
    with mock.patch.object(client._client.chat.completions, "create", return_value=fake_resp) as m:
        resp = client.chat([{"role": "user", "content": "你好"}])
    assert resp.choices[0].message.content == "hi"
    m.assert_called_once()


def test_chat_retries_then_raises_llm_error():
    client = LLMClient(_config())
    with mock.patch.object(
        client._client.chat.completions, "create", side_effect=RuntimeError("boom")
    ) as m, mock.patch("agent.llm.time.sleep") as sleep:
        with pytest.raises(LLMError):
            client.chat([{"role": "user", "content": "x"}], max_retries=3)
    assert m.call_count == 3
    assert sleep.call_count == 2  # 前两次失败各退避一次


def test_chat_succeeds_after_one_retry():
    client = LLMClient(_config())
    fake_resp = mock.Mock(choices=[mock.Mock(message=mock.Mock(content="ok"))])
    with mock.patch.object(
        client._client.chat.completions, "create", side_effect=[RuntimeError("t"), fake_resp]
    ) as m, mock.patch("agent.llm.time.sleep"):
        resp = client.chat([{"role": "user", "content": "x"}], max_retries=3)
    assert resp.choices[0].message.content == "ok"
    assert m.call_count == 2


def test_chat_records_usage():
    client = LLMClient(_config())
    usage = mock.Mock(prompt_tokens=100, completion_tokens=50)
    fake_resp = mock.Mock(
        choices=[mock.Mock(message=mock.Mock(content="hi"))], usage=usage
    )
    with mock.patch.object(client._client.chat.completions, "create", return_value=fake_resp):
        client.chat([{"role": "user", "content": "x"}])
    assert client.usage_summary() == {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
    }
    assert "100" in client.usage_summary_text()
