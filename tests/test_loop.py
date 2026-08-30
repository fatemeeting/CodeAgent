"""loop.py 单元测试：循环终止条件与错误处理（mock LLMClient，免 key）。"""

from unittest import mock

from agent.config import Config
from agent.loop import SYSTEM_PROMPT, run


def test_system_prompt_forbids_markdown_in_code_files():
    assert "纯代码" in SYSTEM_PROMPT
    assert "代码文件" in SYSTEM_PROMPT


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


def test_run_without_emit_prints_logs(capsys, tmp_path):
    """emit=None 时 CLI 打印路径零回归（工具日志走 stdout）。"""
    responses = [
        _response(content=None, tool_calls=[_tool_call()]),
        _response(content="完成"),
    ]
    client = mock.Mock()
    client.chat.side_effect = responses
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_config(), "任务", workdir=str(tmp_path))
    captured = capsys.readouterr().out
    assert "[步骤 1] 调用工具 write_file" in captured
    assert "↳" in captured
    assert out == "完成"


def _stream_config(max_iterations=5):
    return Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=max_iterations,
        stream=True,
    )


def test_run_emits_event_stream(tmp_path):
    responses = [
        _response(content=None, tool_calls=[_tool_call()]),
        _response(content="已创建 a.txt"),
    ]
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        resp = responses.pop(0)
        content = resp.choices[0].message.content
        if on_content and content:
            on_content(content)
        return resp

    client.chat_stream.side_effect = chat_stream
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_stream_config(), "创建 a.txt", workdir=str(tmp_path), emit=events.append)
    types = [e["type"] for e in events]
    assert types[0] == "turn_start" and types[-1] == "turn_end"
    assert "usage" in events[-1]  # turn_end 携带 token 用量
    for t in ("tool_call", "tool_result", "round_end", "content_delta"):
        assert t in types, types
    tr = next(e for e in events if e["type"] == "tool_result")
    assert tr["name"] == "write_file" and tr["ok"] is True and tr["duration_ms"] >= 0
    tc_ev = next(e for e in events if e["type"] == "tool_call")
    assert tc_ev["parameter"] == '{"path": "a.txt", "content": "hi"}'  # 原始 arguments JSON
    # 非正文事件 text 为空，不污染旧前端对话
    assert all(e.get("text", "") == "" for e in events if e["type"] not in ("content_delta", "error"))
    assert out == "已创建 a.txt"


def test_run_emits_think_events():
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        if on_reasoning:
            on_reasoning("先想")
        if on_content:
            on_content("好")
        return _response(content="好")

    client.chat_stream.side_effect = chat_stream
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_stream_config(), "任务", workdir=".", emit=events.append)
    assert [e["type"] for e in events] == [
        "turn_start",
        "think_start",
        "think_delta",
        "content_delta",
        "think_end",
        "round_end",
        "turn_end",
    ]
    assert events[2]["text"] == "先想"


def test_run_emits_untruncated_tool_output(tmp_path):
    """轨迹 tool_result.output 为完整观测（不截断、不折叠），模型上下文仍按 MAX_TOOL_TEXT 截断。"""
    responses = [_response(content=None, tool_calls=[_tool_call()]), _response(content="完成")]
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        resp = responses.pop(0)
        content = resp.choices[0].message.content
        if on_content and content:
            on_content(content)
        return resp

    client.chat_stream.side_effect = chat_stream
    big = "观察行1\n观察行2\n" * 1500  # 15000 字符 > MAX_TOOL_TEXT
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client), mock.patch(
        "agent.loop.dispatch", return_value=big
    ):
        run(_stream_config(), "任务", workdir=str(tmp_path), emit=events.append)
    tr = next(e for e in events if e["type"] == "tool_result")
    assert tr["output"] == big  # 完整多行观测，无截断
    assert "…" not in tr["output"]


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


def test_run_emits_retry_event():
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        if on_retry:
            on_retry(2, 3, RuntimeError("网络错误"))
        return _response(content="完成")

    client.chat_stream.side_effect = chat_stream
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_stream_config(), "任务", workdir=".", emit=events.append)
    retries = [e for e in events if e["type"] == "retry"]
    assert retries and retries[0]["attempt"] == 2 and retries[0]["max"] == 3
    assert "网络错误" in retries[0]["message"]


def test_run_emits_exit_code(tmp_path):
    """execute_command 非零退出码进入 tool_result.exit_code。"""
    call = _tool_call("c1", "execute_command", '{"command": "echo hi"}')
    responses = [_response(content=None, tool_calls=[call]), _response(content="完成")]
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        resp = responses.pop(0)
        if on_content and resp.choices[0].message.content:
            on_content(resp.choices[0].message.content)
        return resp

    client.chat_stream.side_effect = chat_stream
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client), mock.patch(
        "agent.loop.dispatch", return_value="out\n[exit_code: 3]"
    ):
        run(_stream_config(), "任务", workdir=str(tmp_path), emit=events.append)
    tr = next(e for e in events if e["type"] == "tool_result")
    assert tr["exit_code"] == 3


def test_run_param_parse_failure_skips_execution(tmp_path):
    """参数 JSON 解析失败：不执行工具、error 事件化、回填错误观测。"""
    bad = _tool_call("c1", "write_file", "not json{")
    responses = [_response(content=None, tool_calls=[bad]), _response(content="完成")]
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        resp = responses.pop(0)
        if on_content and resp.choices[0].message.content:
            on_content(resp.choices[0].message.content)
        return resp

    client.chat_stream.side_effect = chat_stream
    events = []
    dispatched = mock.Mock()
    with mock.patch("agent.loop.LLMClient", return_value=client), mock.patch(
        "agent.loop.dispatch", dispatched
    ):
        out = run(_stream_config(), "任务", workdir=str(tmp_path), emit=events.append)
    assert out == "完成"
    dispatched.assert_not_called()  # 解析失败不执行
    errs = [e for e in events if e["type"] == "error"]
    assert errs and errs[0]["retryable"] is True and "解析失败" in errs[0]["message"]
    tr = next(e for e in events if e["type"] == "tool_result")
    assert tr["ok"] is False and "解析失败" in tr["output"]


def test_run_with_history_includes_prior_turns():
    """history 前置对话注入本轮（同会话上下文互通）。"""
    client = mock.Mock()
    client.chat.return_value = _response(content="完成")
    history = [
        {"role": "user", "content": "之前的问题"},
        {"role": "assistant", "content": "之前的答复"},
    ]
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_config(), "现在的问题", workdir=".", history=history)
    assert out == "完成"
    messages = client.chat.call_args[0][0]
    roles = [m["role"] for m in messages]
    assert roles[:4] == ["system", "user", "assistant", "user"]  # 历史注入
    assert messages[-1]["role"] == "assistant"  # 本轮答复回填
    assert messages[1]["content"] == "之前的问题"
    assert messages[2]["content"] == "之前的答复"
    assert messages[-2]["content"] == "现在的问题"


def test_run_truncates_long_history():
    """超长历史按 max_context_tokens 截断（保留 system + 首条 user + 最近消息）。"""
    client = mock.Mock()
    client.chat.return_value = _response(content="完成")
    history = []
    for i in range(300):
        history.append({"role": "user", "content": "问题" + str(i)})
        history.append({"role": "assistant", "content": "答复" + str(i)})
    cfg = Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=5,
        max_context_tokens=500,  # 600 条历史远超预算
    )
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(cfg, "现在的问题", workdir=".", history=history)
    messages = client.chat.call_args[0][0]
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "问题0"  # 首条 user 保留
    contents = [m.get("content", "") for m in messages]
    assert "现在的问题" in contents  # 本轮任务始终在
    assert len(messages) < len(history) + 2  # 发生截断


# ---------- goal 模式（迭代 8 · 8.1） ----------

def _goal_config(max_iterations=8):
    return Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=max_iterations,
        goal=True,
    )


def test_goal_auto_continues_until_done():
    responses = [_response(content="我先试试"), _response(content="完成：任务已完成")]
    client = mock.Mock()
    client.chat.side_effect = responses
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_goal_config(), "目标", workdir=".", emit=events.append)
    assert out == "完成：任务已完成"
    assert client.chat.call_count == 2  # 非完成信号自动续跑
    second = client.chat.call_args_list[1].args[0]
    assert any(
        m.get("role") == "user" and "请继续使用工具推进" in m.get("content", "")
        for m in second
    )
    types = [e["type"] for e in events]
    assert "goal_start" in types and "goal_progress" in types and "goal_end" in types


def test_goal_blocked_by_prefix():
    responses = [_response(content="受阻：缺少必要信息")]
    client = mock.Mock()
    client.chat.side_effect = responses
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(_goal_config(), "目标", workdir=".", emit=events.append)
    assert out == "受阻：缺少必要信息"
    goal_types = [e["type"] for e in events if e["type"].startswith("goal")]
    assert goal_types == ["goal_start", "goal_blocked", "goal_end"]


def test_goal_stalls_after_three_rounds():
    responses = [_response(content="还在尝试")] * 5
    client = mock.Mock()
    client.chat.side_effect = responses
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_goal_config(), "目标", workdir=".", emit=events.append)
    blocked = [e for e in events if e["type"] == "goal_blocked"]
    assert blocked and "无进展" in blocked[0]["reason"]
    assert client.chat.call_count == 3  # 3 轮无进展即止


def test_run_emits_todo_snapshot_event(tmp_path):
    """todo_write 成功后发 todo 事件（清单快照）。"""
    call = _tool_call("c1", "todo_write", '{"todos": [{"id": "1", "content": "步骤A", "status": "in_progress"}]}')
    responses = [_response(content=None, tool_calls=[call]), _response(content="完成")]
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        resp = responses.pop(0)
        if on_content and resp.choices[0].message.content:
            on_content(resp.choices[0].message.content)
        return resp

    client.chat_stream.side_effect = chat_stream
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_stream_config(), "任务", workdir=str(tmp_path), emit=events.append)
    todo_evs = [e for e in events if e["type"] == "todo"]
    assert len(todo_evs) == 1
    assert todo_evs[0]["todos"] == [{"id": "1", "content": "步骤A", "status": "in_progress"}]


def test_run_emits_subagent_events(tmp_path):
    """delegate_subagent 调用前后发 subagent_start/subagent_end 事件。"""
    call = _tool_call("c1", "delegate_subagent", '{"task": "独立子任务", "name": "辅助"}')
    responses = [_response(content=None, tool_calls=[call]), _response(content="完成")]
    client = mock.Mock()

    def chat_stream(messages, tools=None, on_content=None, on_reasoning=None, on_retry=None):
        resp = responses.pop(0)
        if on_content and resp.choices[0].message.content:
            on_content(resp.choices[0].message.content)
        return resp

    client.chat_stream.side_effect = chat_stream
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client), mock.patch(
        "agent.loop.run", return_value="子代理结果"
    ):
        run(_stream_config(), "任务", workdir=str(tmp_path), emit=events.append)
    starts = [e for e in events if e["type"] == "subagent_start"]
    ends = [e for e in events if e["type"] == "subagent_end"]
    assert len(starts) == 1 and starts[0]["name"] == "辅助" and "独立子任务" in starts[0]["task"]
    assert len(ends) == 1 and ends[0]["ok"] is True and "子代理结果" in ends[0]["summary"]


# ---------- 上下文压缩（迭代 8 · 8.4） ----------

def _big_history(n=300):
    history = []
    for i in range(n):
        history.append({"role": "user", "content": "问题" + str(i)})
        history.append({"role": "assistant", "content": "答复" + str(i)})
    return history


def test_run_compacts_long_history():
    """超预算 80% 时旧轮次被压缩为摘要（compact 事件 + 摘要注入）。"""
    cfg = Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=5,
        max_context_tokens=400,
        stream=True,
    )
    client = mock.Mock()
    client.chat.return_value = _response("压缩摘要内容")
    client.chat_stream.return_value = _response("完成")
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(cfg, "现在的问题", workdir=".", emit=events.append, history=_big_history())
    assert out == "完成"
    compacts = [e for e in events if e["type"] == "compact"]
    assert len(compacts) == 1
    assert compacts[0]["before"] > compacts[0]["after"]
    messages = client.chat_stream.call_args[0][0]
    assert any("[上下文压缩摘要] 压缩摘要内容" in m.get("content", "") for m in messages)


def test_run_cli_skips_compaction():
    """emit=None（CLI）不触发压缩额外 LLM 调用。"""
    cfg = Config(
        api_key="k",
        base_url="https://example.com",
        model="deepseek-chat",
        max_iterations=5,
        max_context_tokens=400,
    )
    client = mock.Mock()
    client.chat.side_effect = [_response("完成")]
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(cfg, "现在的问题", workdir=".", history=_big_history())
    assert out == "完成"
    assert client.chat.call_count == 1  # 仅主循环一次，无压缩调用


# ---------- chat/agent 双模式（迭代 8 · 8.6） ----------

def test_run_chat_mode_uses_readonly_tools():
    """chat 模式：system 明示只读约束 + 调用方传入只读工具集。"""
    from agent.tools import READ_ONLY_TOOL_NAMES, tool_schemas_for

    client = mock.Mock()
    client.chat.return_value = _response("完成")
    with mock.patch("agent.loop.LLMClient", return_value=client):
        out = run(
            _config(), "你好", workdir=".", mode="chat",
            tools=tool_schemas_for(READ_ONLY_TOOL_NAMES),
        )
    assert out == "完成"
    messages, kwargs = client.chat.call_args[0][0], client.chat.call_args[1]
    assert "chat 模式" in messages[0]["content"] and "不能修改文件" in messages[0]["content"]
    tool_names = {t["function"]["name"] for t in kwargs.get("tools") or []}
    assert tool_names == {"read_file", "list_directory", "search_content", "web_search"}


def test_run_agent_mode_defaults_all_tools():
    client = mock.Mock()
    client.chat.return_value = _response("完成")
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_config(), "你好", workdir=".")
    kwargs = client.chat.call_args[1]
    tool_names = {t["function"]["name"] for t in kwargs.get("tools") or []}
    assert "write_file" in tool_names and "delegate_subagent" in tool_names  # 全工具


# ---------- 技能显式注入（迭代 9 · 9.2） ----------

def test_run_injects_explicit_skills():
    """仅显式传入的技能注入 system；无 skills 时不注入。"""
    from agent.skills import Skill

    skill = Skill(name="demo", description="演示技能", body="指南正文")
    client = mock.Mock()
    client.chat.return_value = _response("完成")
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_config(), "任务", workdir=".", skills=[skill])
    system = client.chat.call_args[0][0][0]["content"]
    assert "已装载技能" in system and "技能：demo" in system and "指南正文" in system
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_config(), "任务", workdir=".")
    system2 = client.chat.call_args[0][0][0]["content"]
    assert "已装载技能" not in system2  # 未指定不注入


def test_run_emits_skill_loaded():
    from agent.skills import Skill

    skill = Skill(name="demo", description="演示技能", body="正文")
    client = mock.Mock()
    client.chat_stream.return_value = _response("完成")
    events = []
    with mock.patch("agent.loop.LLMClient", return_value=client):
        run(_stream_config(), "任务", workdir=".", emit=events.append, skills=[skill])
    loaded = [e for e in events if e["type"] == "skill_loaded"]
    assert len(loaded) == 1
    assert loaded[0]["name"] == "demo" and loaded[0]["description"] == "演示技能"


def test_cli_harden_stdio_replaces_unencodable(monkeypatch):
    """管道重定向下 GBK 不可编码字符（如 ↳）不再崩溃（errors=replace）。"""
    import io
    import sys

    from agent import cli

    raw = io.BytesIO()
    wrapper = io.TextIOWrapper(raw, encoding="gbk", errors="strict")
    monkeypatch.setattr(sys, "stdout", wrapper)
    cli._harden_stdio()
    print("↳ 观测")  # 修复前抛 UnicodeEncodeError
    wrapper.flush()
    assert "?" in raw.getvalue().decode("gbk")  # 被替换为 ?，而不是崩溃
