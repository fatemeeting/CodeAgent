"""loop.py 单元测试：循环终止条件与错误处理（mock LLMClient，免 key）。"""

from unittest import mock

from agent.config import Config
from agent.loop import run


def _config(max_iterations=5):
    return Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=max_iterations,
    )


def _tool_call(cid="c1", name="write_file", args='{"path": "a.txt", "content": "hi"}'):
    fn = mock.Mock()
    fn.name = name
    fn.arguments = args
    tc = mock.Mock()
    tc.id = cid
    tc.function = fn
    return tc


def _response(content=None, tool_calls=None):
    msg = mock.Mock()
    msg.content = content
    msg.tool_calls = tool_calls
    choice = mock.Mock()
    choice.message = msg
    resp = mock.Mock()
    resp.choices = [choice]
    return resp


def test_run_text_only_returns_content():
    client = mock.Mock()
    client.chat.return_value = _response(content="完成")
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_config(), "任务", workdir=".")
    assert out == "完成"
    client.chat.assert_called_once()


def test_run_executes_tool_then_final(tmp_path):
    responses = [
        _response(content=None, tool_calls=[_tool_call()]),
        _response(content="已创建 a.txt"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_config(), "创建 a.txt", workdir=str(tmp_path))
    assert out == "已创建 a.txt"
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "hi"
    assert client.chat.call_count == 2
    second_messages = client.chat.call_args_list[1].args[0]
    assert any(m.get("role") == "tool" and m.get("tool_call_id") == "c1" for m in second_messages)


def test_run_stops_at_max_iterations():
    responses = [
        _response(content=None, tool_calls=[_tool_call(f"c{i}", "list_directory", "{}")])
        for i in range(3)
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_config(max_iterations=3), "任务", workdir=".")
    assert "最大迭代" in out
    assert client.chat.call_count == 3


def test_run_tool_error_becomes_observation(tmp_path):
    bad_call = _tool_call("c1", "write_file", '{"path": "a.txt"}')  # 缺 content → KeyError
    responses = [
        _response(content=None, tool_calls=[bad_call]),
        _response(content="已处理"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_config(), "任务", workdir=str(tmp_path))
    assert out == "已处理"
    second_messages = client.chat.call_args_list[1].args[0]
    tool_msg = next(m for m in second_messages if m.get("role") == "tool")
    assert "错误" in tool_msg["content"]


def _reflect_config(max_iterations=5):
    return Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=max_iterations,
        reflect=True,
    )


def test_run_reflect_confirms_then_returns_original():
    responses = [
        _response(content="A"),
        _response(content="已确认完成"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_reflect_config(), "任务", workdir=".")
    assert out == "A"  # 返回原始答复（更详细）
    assert client.chat.call_count == 2


def test_run_reflect_finds_issue_then_fixes(tmp_path):
    responses = [
        _response(content="A"),
        _response(content=None, tool_calls=[_tool_call("c1", "write_file", '{"path": "a.txt", "content": "fixed"}')]),
        _response(content="B"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_reflect_config(), "任务", workdir=str(tmp_path))
    assert out == "B"
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "fixed"
    assert client.chat.call_count == 3


def test_run_stream_uses_chat_stream():
    client = mock.Mock()
    client.chat_stream.return_value = _response(content="完成")
    cfg = Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=5,
        stream=True,
    )
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(cfg, "任务", workdir=".")
    assert out == "完成"
    client.chat_stream.assert_called_once()
    client.chat.assert_not_called()


def test_run_executes_multiple_tool_calls(tmp_path):
    calls = [
        _tool_call("c1", "write_file", '{"path": "a.txt", "content": "A"}'),
        _tool_call("c2", "write_file", '{"path": "b.txt", "content": "B"}'),
    ]
    responses = [
        _response(content=None, tool_calls=calls),
        _response(content="完成"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_config(), "创建两个文件", workdir=str(tmp_path))
    assert out == "完成"
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "A"
    assert (tmp_path / "b.txt").read_text(encoding="utf-8") == "B"
    second_messages = client.chat.call_args_list[1].args[0]
    tool_ids = [m["tool_call_id"] for m in second_messages if m.get("role") == "tool"]
    assert tool_ids == ["c1", "c2"]  # 观测按调用顺序回填


def _confirm_config(max_iterations=5):
    return Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=max_iterations,
        confirm_dangerous=True,
    )


def test_run_confirm_dangerous_declined(tmp_path):
    call = _tool_call("c1", "execute_command", '{"command": "rm -rf x"}')
    responses = [
        _response(content=None, tool_calls=[call]),
        _response(content="好的"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client), mock.patch(
        "builtins.input", return_value="n"
    ):
        out = run(_confirm_config(), "删除文件", workdir=str(tmp_path))
    assert out == "好的"
    second_messages = client.chat.call_args_list[1].args[0]
    tool_msg = next(m for m in second_messages if m.get("role") == "tool")
    assert "取消" in tool_msg["content"]


def test_run_confirm_dangerous_approved(tmp_path):
    import json as _json
    import sys as _sys

    (tmp_path / "x.txt").write_text("data", encoding="utf-8")
    # 跨平台删除命令（Windows/ubuntu 均可用），且命中 os.remove 危险模式
    cmd = f'"{_sys.executable}" -c "import os; os.remove(\'x.txt\')"'
    call = _tool_call("c1", "execute_command", _json.dumps({"command": cmd}))
    responses = [
        _response(content=None, tool_calls=[call]),
        _response(content="完成"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client), mock.patch(
        "builtins.input", return_value="y"
    ):
        out = run(_confirm_config(), "删除 x.txt", workdir=str(tmp_path))
    assert out == "完成"
    assert not (tmp_path / "x.txt").exists()  # 确认后实际执行


def test_run_logs_tool_calls(capsys, tmp_path):
    responses = [
        _response(content=None, tool_calls=[_tool_call()]),
        _response(content="完成"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_config(), "创建 a.txt", workdir=str(tmp_path))
    out = capsys.readouterr().out
    assert "调用工具 write_file" in out
    assert "↳" in out
