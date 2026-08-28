"""context.py 单元测试：token 估算与历史裁剪、持久化。"""

import pytest

from agent.context import estimate_tokens, load_history, save_history, truncate_history


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


def test_estimate_tokens_ascii_and_cjk():
    assert estimate_tokens("hello world") >= 2  # 11 个 ASCII / 4 ≈ 2
    assert estimate_tokens("你好世界") >= 4  # 4 个 CJK 字符 ≈ 4


def test_truncate_keeps_system_and_task():
    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "a" * 1000},
    ]
    out = truncate_history(msgs, max_tokens=10)
    assert [m["role"] for m in out] == ["system", "user"]


def test_truncate_drops_middle_keeps_recent():
    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "old" * 100},
        {"role": "tool", "tool_call_id": "x", "content": "old result"},
        {"role": "assistant", "content": "recent"},
    ]
    out = truncate_history(msgs, max_tokens=20)
    assert [m["role"] for m in out] == ["system", "user", "assistant"]
    assert out[-1]["content"] == "recent"


def test_truncate_under_budget_keeps_all():
    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "ok"},
    ]
    assert truncate_history(msgs, max_tokens=1000) == msgs


def test_truncate_drops_leading_orphan_tool():
    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "a" * 200, "tool_calls": []},
        {"role": "tool", "tool_call_id": "c1", "content": "result"},
        {"role": "assistant", "content": "recent"},
    ]
    out = truncate_history(msgs, max_tokens=6)
    assert [m["role"] for m in out] == ["system", "user", "assistant"]
    assert out[-1]["content"] == "recent"


def test_truncate_empty():
    assert truncate_history([], 100) == []


def test_save_load_history_roundtrip(tmp_path):
    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "任务"},
        {"role": "assistant", "content": "答复"},
    ]
    p = tmp_path / "history.json"
    save_history(msgs, str(p))
    assert load_history(str(p)) == msgs


def test_load_history_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_history(str(tmp_path / "nope.json"))


def test_load_history_bad_format(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{}", encoding="utf-8")  # 非列表
    with pytest.raises(ValueError):
        load_history(str(p))
