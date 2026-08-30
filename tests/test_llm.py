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


def test_chat_stream_reconstructs_response(capsys):
    from agent.parser import parse_response

    client = LLMClient(_config())
    chunk1 = mock.Mock()
    chunk1.usage = None
    chunk1.choices = [mock.Mock(delta=mock.Mock(content="你", tool_calls=None))]
    chunk2 = mock.Mock()
    chunk2.usage = None
    chunk2.choices = [mock.Mock(delta=mock.Mock(content="好", tool_calls=None))]
    with mock.patch.object(
        client._client.chat.completions, "create", return_value=iter([chunk1, chunk2])
    ):
        resp = client.chat_stream([{"role": "user", "content": "x"}])
    parsed = parse_response(resp)
    assert parsed.content == "你好"
    assert capsys.readouterr().out == "你好\n"  # 逐 token 打印 + 换行


def _reasoning_chunks():
    def mk(content=None, reasoning=None):
        return mock.Mock(
            usage=None,
            choices=[mock.Mock(delta=mock.Mock(content=content, reasoning_content=reasoning, tool_calls=None))],
        )

    return [mk(reasoning="先思考"), mk(reasoning="一下"), mk(content="好")]


def test_chat_stream_captures_reasoning(capsys):
    client = LLMClient(_config())
    reasoning_cb = []
    content_cb = []
    with mock.patch.object(
        client._client.chat.completions, "create", return_value=iter(_reasoning_chunks())
    ):
        resp = client.chat_stream(
            [{"role": "user", "content": "x"}],
            on_reasoning=reasoning_cb.append,
            on_content=content_cb.append,
        )
    assert resp.reasoning == "先思考一下"
    assert reasoning_cb == ["先思考", "一下"]
    assert content_cb == ["好"]
    assert capsys.readouterr().out == ""  # 回调模式下不打印


def test_chat_attaches_reasoning_content():
    client = LLMClient(_config())
    fake_resp = mock.Mock(
        choices=[mock.Mock(message=mock.Mock(content="hi", reasoning_content="深度思考"))]
    )
    with mock.patch.object(client._client.chat.completions, "create", return_value=fake_resp):
        resp = client.chat([{"role": "user", "content": "x"}])
    assert resp.reasoning == "深度思考"


def test_chat_retry_callback():
    client = LLMClient(_config())
    fake_resp = mock.Mock(choices=[mock.Mock(message=mock.Mock(content="ok"))])
    calls = []
    with mock.patch.object(
        client._client.chat.completions, "create", side_effect=[RuntimeError("t"), fake_resp]
    ) as m, mock.patch("agent.llm.time.sleep"):
        resp = client.chat(
            [{"role": "user", "content": "x"}],
            max_retries=3,
            on_retry=lambda attempt, mx, exc: calls.append((attempt, mx, str(exc))),
        )
    assert resp.choices[0].message.content == "ok"
    assert m.call_count == 2
    assert calls == [(1, 3, "t")]  # 重试前回调：第 1 次失败、attempt=1
