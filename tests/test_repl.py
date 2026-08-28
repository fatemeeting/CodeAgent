"""repl.py 单元测试：命令解析 + 交互循环（mock input，免 key）。"""

from unittest import mock

from agent.config import Config
from agent.repl import interpret, repl


def _config():
    return Config(
        api_key="k", base_url="https://example.com", model="deepseek-chat", max_iterations=5
    )


def _response(content="完成"):
    msg = mock.Mock()
    msg.content = content
    msg.tool_calls = None
    choice = mock.Mock()
    choice.message = msg
    resp = mock.Mock()
    resp.choices = [choice]
    return resp


def test_interpret_commands():
    assert interpret("") == ("empty", None)
    assert interpret("   ") == ("empty", None)
    assert interpret("/quit") == ("quit", None)
    assert interpret("/exit") == ("quit", None)
    assert interpret("/help") == ("help", None)
    assert interpret("/clear") == ("clear", None)
    assert interpret("/history") == ("history", None)
    assert interpret("创建文件") == ("task", "创建文件")


def test_repl_quit(capsys):
    with mock.patch("builtins.input", side_effect=["/quit"]):
        assert repl(_config(), workdir=".") == 0
    assert "再见" in capsys.readouterr().out


def test_repl_runs_task_then_quit(capsys):
    client = mock.Mock()
    client.chat.return_value = _response("完成")
    with mock.patch("builtins.input", side_effect=["创建文件", "/quit"]), mock.patch(
        "agent.repl.LLMClient", return_value=client
    ):
        assert repl(_config(), workdir=".") == 0
    out = capsys.readouterr().out
    assert "完成" in out


def test_repl_history_and_clear(capsys):
    with mock.patch("builtins.input", side_effect=["/history", "/clear", "/history", "/quit"]):
        repl(_config(), workdir=".")
    out = capsys.readouterr().out
    assert "1 条消息" in out  # 初始仅 system


def test_interpret_save_load():
    assert interpret("/save") == ("save", "history.json")
    assert interpret("/save foo.json") == ("save", "foo.json")
    assert interpret("/load") == ("load", "history.json")
    assert interpret("/load bar.json") == ("load", "bar.json")


def test_repl_save_writes_file(tmp_path):
    import json

    path = str(tmp_path / "h.json")
    with mock.patch("builtins.input", side_effect=[f"/save {path}", "/quit"]):
        repl(_config(), workdir=".")
    data = json.loads(open(path, encoding="utf-8").read())
    assert len(data) == 1
    assert data[0]["role"] == "system"
