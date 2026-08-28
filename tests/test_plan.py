"""plan.py 单元测试：任务规划（mock，免 key）。"""

from unittest import mock

from agent.plan import make_plan


def _response(content):
    msg = mock.Mock()
    msg.content = content
    msg.tool_calls = None
    choice = mock.Mock()
    choice.message = msg
    resp = mock.Mock()
    resp.choices = [choice]
    return resp


def test_make_plan_returns_content():
    client = mock.Mock()
    client.chat.return_value = _response("1. 创建文件\n2. 运行验证")
    out = make_plan(client, "创建并运行脚本")
    assert out == "1. 创建文件\n2. 运行验证"
    client.chat.assert_called_once()
