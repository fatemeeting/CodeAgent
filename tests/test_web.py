"""web.py 单元测试：输出捕获 + HTTP 服务（mock LLM，免 key）。"""

import json
import threading
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

from agent.config import Config
from agent.web import AgentHandler, run_task_output


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


def test_run_task_output_captures_stdout():
    client = mock.Mock()
    client.chat.return_value = _response("完成")
    with mock.patch("agent.web.LLMClient", return_value=client):
        out = run_task_output(_config(), "任务", workdir=".")
    assert "完成" in out  # 过程日志 + 最终答复都被捕获


def test_web_server_roundtrip():
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    client = mock.Mock()
    client.chat.return_value = _response("完成")
    try:
        with mock.patch("agent.web.LLMClient", return_value=client):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as resp:
                assert "编程智能体" in resp.read().decode("utf-8")
            data = json.dumps({"task": "你好"}).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/run",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            assert result["ok"] is True
            assert "完成" in result["output"]
    finally:
        server.shutdown()
        server.server_close()


def test_web_run_rejects_missing_workdir(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    client = mock.Mock()
    client.chat.return_value = _response("完成")
    try:
        with mock.patch("agent.web.LLMClient", return_value=client):
            data = json.dumps({"task": "你好", "workdir": str(tmp_path / "nope")}).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/run",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            assert result["ok"] is False
            assert "工作区不存在" in result["error"]
    finally:
        server.shutdown()
        server.server_close()


def test_web_pick_workspace(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        with mock.patch("agent.web.pick_workspace", return_value=str(tmp_path)):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/pick-workspace",
                data=b"{}",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            assert result["ok"] is True
            assert result["path"] == str(tmp_path)
        # 未选择时优雅降级
        with mock.patch("agent.web.pick_workspace", return_value=None):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/pick-workspace",
                data=b"{}",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            assert result["ok"] is False
            assert "无法唤起" in result["error"]
    finally:
        server.shutdown()
        server.server_close()


def test_web_sse_stream():
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    client = mock.Mock()
    client.chat.return_value = _response("完成")
    try:
        with mock.patch("agent.web.LLMClient", return_value=client):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/events?task=hi") as resp:
                raw = resp.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
    assert "data:" in raw
    assert "完成" in raw
    assert "[DONE]" in raw


def test_web_tree(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    (tmp_path / "a.py").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    try:
        url = f"http://127.0.0.1:{port}/tree?workdir=" + urllib.parse.quote(str(tmp_path))
        with urllib.request.urlopen(url) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        assert result["ok"] is True
        names = [e["name"] for e in result["tree"]]
        assert "a.py" in names and "sub" in names
        bad = f"http://127.0.0.1:{port}/tree?workdir=" + urllib.parse.quote(str(tmp_path / "nope"))
        with urllib.request.urlopen(bad) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        assert result["ok"] is False
    finally:
        server.shutdown()
        server.server_close()
