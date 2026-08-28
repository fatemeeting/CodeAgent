"""suggest.py 单元测试：猜你想问（mock，免 key）。"""

from unittest import mock

from agent.suggest import suggest_followups


def _response(content):
    msg = mock.Mock()
    msg.content = content
    msg.tool_calls = None
    choice = mock.Mock()
    choice.message = msg
    resp = mock.Mock()
    resp.choices = [choice]
    return resp


def test_suggest_returns_content():
    client = mock.Mock()
    client.chat.return_value = _response("1. 问题一\n2. 问题二")
    out = suggest_followups(client, "创建文件")
    assert out == "1. 问题一\n2. 问题二"
    client.chat.assert_called_once()
