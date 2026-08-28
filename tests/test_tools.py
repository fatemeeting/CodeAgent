"""工具层单元测试：全程不调用任何模型 API（mock 自由、免 key）。"""

import sys

from agent.tools import TOOLS, dispatch, tool_schemas
from agent.tools.shell_tools import is_dangerous


def test_six_tools_registered():
    names = {t.name for t in TOOLS}
    assert names == {
        "read_file",
        "write_file",
        "edit_file",
        "execute_command",
        "list_directory",
        "search_content",
    }


def test_schemas_are_valid():
    for schema in tool_schemas():
        assert schema["type"] == "function"
        fn = schema["function"]
        assert fn["name"]
        assert fn["description"]
        assert fn["parameters"]["type"] == "object"
        for required in fn["parameters"].get("required", []):
            assert required in fn["parameters"]["properties"]


def test_read_write_edit_roundtrip(tmp_path):
    wd = str(tmp_path)
    dispatch("write_file", {"path": "a.txt", "content": "hello world"}, wd)
    assert dispatch("read_file", {"path": "a.txt"}, wd) == "hello world"
    dispatch("edit_file", {"path": "a.txt", "old_string": "world", "new_string": "agent"}, wd)
    assert dispatch("read_file", {"path": "a.txt"}, wd) == "hello agent"


def test_read_missing_file_returns_error(tmp_path):
    out = dispatch("read_file", {"path": "nope.txt"}, str(tmp_path))
    assert "错误" in out and "不存在" in out


def test_edit_multiple_matches_requires_replace_all(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("x x x", encoding="utf-8")
    out = dispatch("edit_file", {"path": "a.txt", "old_string": "x", "new_string": "y"}, str(tmp_path))
    assert "匹配到 3 处" in out
    dispatch(
        "edit_file",
        {"path": "a.txt", "old_string": "x", "new_string": "y", "replace_all": True},
        str(tmp_path),
    )
    assert p.read_text(encoding="utf-8") == "y y y"


def test_list_directory(tmp_path):
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    out = dispatch("list_directory", {"path": "."}, str(tmp_path))
    assert "b.txt" in out and "sub/" in out


def test_search_content(tmp_path):
    (tmp_path / "x.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    out = dispatch("search_content", {"query": "foo", "path": "."}, str(tmp_path))
    assert "x.py:1:" in out


def test_execute_command(tmp_path):
    out = dispatch("execute_command", {"command": "echo hello", "timeout": 10}, str(tmp_path))
    assert "hello" in out
    assert "[exit_code: 0]" in out


def test_execute_command_captures_failure(tmp_path):
    cmd = f'"{sys.executable}" -c "import sys; sys.exit(3)"'
    out = dispatch("execute_command", {"command": cmd, "timeout": 15}, str(tmp_path))
    assert "[exit_code: 3]" in out


def test_dispatch_unknown_tool(tmp_path):
    out = dispatch("no_such_tool", {}, str(tmp_path))
    assert "未知工具" in out


def test_is_dangerous():
    assert is_dangerous("rm -rf x")
    assert is_dangerous("del file.txt")
    assert is_dangerous("git push origin main")
    assert is_dangerous('python -c "import os; os.remove(\'x\')"')  # 堵绕过
    assert not is_dangerous("echo hello")
    assert not is_dangerous("python main.py")
