"""web.py 单元测试：输出捕获 + HTTP 服务（mock LLM，免 key）。"""

import json
import threading
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

from agent.config import Config
from agent.sessions import SessionStore
from agent.web import AgentHandler, _history_from_session, run_task_output


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

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        if on_content:
            on_content("完成")
        return _response("完成")

    client.chat_stream = mock.Mock(side_effect=chat_stream)
    try:
        with mock.patch("agent.web.LLMClient", return_value=client):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/events?task=hi") as resp:
                raw = resp.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
    assert "data:" in raw
    assert '"type": "content_delta"' in raw
    assert "完成" in raw
    assert "[DONE]" in raw


def test_web_sse_streams_incrementally():
    """配置 stream=False 时 Web 仍逐块推送事件帧（强制流式 + think 事件）。"""
    import time as _time

    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()  # stream=False（默认）
    server.workdir = "."
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        if on_reasoning:
            on_reasoning("想一下")
        for piece in ["你", "好", "，", "世界"]:
            if on_content:
                on_content(piece)
            _time.sleep(0.05)
        return _response("你好，世界")

    client.chat_stream = mock.Mock(side_effect=chat_stream)
    frames = []
    try:
        with mock.patch("agent.web.LLMClient", return_value=client):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/events?task=hi") as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        frames.append(line[6:])
    finally:
        server.shutdown()
        server.server_close()
    assert frames[-1] == "[DONE]"
    events = [json.loads(f) for f in frames[:-1]]
    chunks = [e["text"] for e in events if e["type"] == "content_delta"]
    assert chunks == ["你", "好", "，", "世界"], chunks  # 逐块到达、顺序一致
    think = [e for e in events if e["type"] == "think_delta"]
    assert think and think[0]["text"] == "想一下"
    assert any(e["type"] == "round_end" for e in events)


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


def test_web_file(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    (tmp_path / "a.py").write_text("print(1)", encoding="utf-8")
    base = f"http://127.0.0.1:{port}/file?workdir=" + urllib.parse.quote(str(tmp_path)) + "&path="
    try:
        with urllib.request.urlopen(base + "a.py") as resp:
            result = json.loads(resp.read().decode("utf-8"))
        assert result["ok"] is True
        assert result["content"] == "print(1)"
        assert result["name"] == "a.py"
        # 不存在
        with urllib.request.urlopen(base + "nope.py") as resp:
            result = json.loads(resp.read().decode("utf-8"))
        assert result["ok"] is False
        # 越界
        with urllib.request.urlopen(base + urllib.parse.quote("../outside.py")) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        assert result["ok"] is False
        assert "越界" in result["error"]
    finally:
        server.shutdown()
        server.server_close()


def test_web_exec(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = str(tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    def post(payload):
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/exec",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        r = post({"workdir": str(tmp_path), "command": "echo hi"})
        assert r["ok"] is True
        assert "hi" in r["output"]
        assert r["dangerous"] is False
        r = post({"workdir": str(tmp_path), "command": "rm"})
        assert r["ok"] is True
        assert r["dangerous"] is True
        r = post({"workdir": str(tmp_path / "nope"), "command": "echo x"})
        assert r["ok"] is False
    finally:
        server.shutdown()
        server.server_close()


def test_web_save_file(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    (tmp_path / "a.py").write_text("old", encoding="utf-8")

    def post(payload):
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/save-file",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        # 覆盖写入
        r = post({"workdir": str(tmp_path), "path": "a.py", "content": "print(2)"})
        assert r["ok"] is True and r["name"] == "a.py"
        assert (tmp_path / "a.py").read_text(encoding="utf-8") == "print(2)"
        # 子目录新建
        r = post({"workdir": str(tmp_path), "path": "sub/b.py", "content": "x"})
        assert r["ok"] is True
        assert (tmp_path / "sub" / "b.py").read_text(encoding="utf-8") == "x"
        # 越界拒绝
        r = post({"workdir": str(tmp_path), "path": "../evil.py", "content": "bad"})
        assert r["ok"] is False
        assert "越界" in r["error"]
        assert not (tmp_path.parent / "evil.py").exists()
        # 工作区不存在
        r = post({"workdir": str(tmp_path / "nope"), "path": "a.py", "content": "x"})
        assert r["ok"] is False
        # 缺少 path
        r = post({"workdir": str(tmp_path), "content": "x"})
        assert r["ok"] is False
    finally:
        server.shutdown()
        server.server_close()


def test_web_sessions(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    server.sessions = SessionStore(tmp_path / "data" / "sessions")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    base = f"http://127.0.0.1:{port}"

    def post(path, payload):
        req = urllib.request.Request(
            base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get(path):
        with urllib.request.urlopen(base + path) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        # 新建
        r = post("/sessions", {"workspace": str(tmp_path), "name": "会话A"})
        assert r["ok"] is True
        sid = r["session"]["id"]
        # 列表
        r = get("/sessions")
        assert r["ok"] is True and any(s["id"] == sid for s in r["sessions"])
        # 详情
        r = get(f"/sessions/{sid}")
        assert r["ok"] is True and r["session"]["name"] == "会话A"
        # 存消息
        r = post(f"/sessions/{sid}/messages", {"messages": [{"role": "user", "content": "x"}]})
        assert r["ok"] is True and len(r["session"]["messages"]) == 1
        # 重命名
        r = post(f"/sessions/{sid}", {"name": "改名"})
        assert r["ok"] is True and r["session"]["name"] == "改名"
        # 非法 id
        r = get("/sessions/nope")
        assert r["ok"] is False
        # 删除
        req = urllib.request.Request(base + f"/sessions/{sid}", method="DELETE")
        with urllib.request.urlopen(req) as resp:
            r = json.loads(resp.read().decode("utf-8"))
        assert r["ok"] is True
        assert get("/sessions")["sessions"] == []
    finally:
        server.shutdown()
        server.server_close()


def test_history_from_session_skips_placeholder_and_current_task():
    session = {
        "messages": [
            {"role": "user", "raw": "第一问"},
            {"role": "agent", "raw": "第一答"},
            {"role": "user", "raw": "当前任务"},
            {"role": "agent", "raw": ""},  # 流式占位
        ]
    }
    hist = _history_from_session(session, "当前任务")
    assert hist == [
        {"role": "user", "content": "第一问"},
        {"role": "assistant", "content": "第一答"},
    ]
    assert _history_from_session(None, "x") == []  # 无会话


def test_web_sse_uses_session_history(tmp_path):
    """/events?session= 注入会话前置历史（同会话上下文互通）。"""
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    server.sessions = SessionStore(tmp_path / "data" / "sessions")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    client = mock.Mock()
    captured = {}

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        captured["messages"] = [dict(m) for m in messages]
        if on_content:
            on_content("完成")
        return _response("完成")

    client.chat_stream = mock.Mock(side_effect=chat_stream)
    s = server.sessions.create_session(str(tmp_path), "会话")
    server.sessions.save_messages(s["id"], [
        {"role": "user", "raw": "之前的问题"},
        {"role": "agent", "raw": "之前的答复"},
        {"role": "user", "raw": "现在的问题"},  # 当前任务（剔除防重复）
        {"role": "agent", "raw": ""},           # 空占位（跳过）
    ])
    try:
        with mock.patch("agent.web.LLMClient", return_value=client):
            url = (
                f"http://127.0.0.1:{port}/events?task="
                + urllib.parse.quote("现在的问题")
                + "&session="
                + s["id"]
            )
            with urllib.request.urlopen(url) as resp:
                raw = resp.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
    msgs = captured["messages"]
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    assert msgs[1]["content"] == "之前的问题"
    assert msgs[2]["content"] == "之前的答复"
    assert msgs[-1]["content"] == "现在的问题"
    assert "完成" in raw and "[DONE]" in raw


def test_web_sessions_filter_by_workspace(tmp_path):
    """GET /sessions?workspace= 仅返回该工作区的会话（会话归属工作区）。"""
    server = ThreadingHTTPServer(("127.0.0.1", 0), AgentHandler)
    server.config = _config()
    server.workdir = "."
    server.sessions = SessionStore(tmp_path / "data" / "sessions")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    base = f"http://127.0.0.1:{port}"

    def post(path, payload):
        req = urllib.request.Request(
            base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get(path):
        with urllib.request.urlopen(base + path) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        a = post("/sessions", {"workspace": "E:/demoA", "name": "A"})["session"]
        post("/sessions", {"workspace": "E:/demoB", "name": "B"})
        r = get("/sessions?workspace=" + urllib.parse.quote("E:/demoA"))
        assert r["ok"] is True
        assert [s["id"] for s in r["sessions"]] == [a["id"]]
        assert len(get("/sessions")["sessions"]) == 2  # 无参数返回全部
    finally:
        server.shutdown()
        server.server_close()
