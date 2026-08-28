"""parser.py 单元测试：文本 / tool_calls 分流与参数解析（mock 响应对象，免 key）。"""

from unittest import mock

from agent.parser import parse_response


def _response(content=None, tool_calls=None):
    msg = mock.Mock()
    msg.content = content
    msg.tool_calls = tool_calls
    choice = mock.Mock()
    choice.message = msg
    resp = mock.Mock()
    resp.choices = [choice]
    return resp


def _tool_call(cid="c1", name="read_file", args='{"path": "x.txt"}'):
    fn = mock.Mock()
    fn.name = name
    fn.arguments = args
    tc = mock.Mock()
    tc.id = cid
    tc.function = fn
    return tc


def test_parse_text_only():
    parsed = parse_response(_response(content="你好"))
    assert parsed.content == "你好"
    assert parsed.tool_calls == []


def test_parse_tool_calls():
    parsed = parse_response(_response(content=None, tool_calls=[_tool_call()]))
    assert len(parsed.tool_calls) == 1
    assert parsed.tool_calls[0].id == "c1"
    assert parsed.tool_calls[0].name == "read_file"
    assert parsed.tool_calls[0].arguments == {"path": "x.txt"}
    assert parsed.tool_calls[0].arguments_raw == '{"path": "x.txt"}'


def test_parse_malformed_arguments():
    parsed = parse_response(_response(content=None, tool_calls=[_tool_call(args="not-json")]))
    assert "_error" in parsed.tool_calls[0].arguments


def test_parse_empty_response():
    resp = mock.Mock()
    resp.choices = []
    parsed = parse_response(resp)
    assert parsed.content == ""
    assert parsed.tool_calls == []
