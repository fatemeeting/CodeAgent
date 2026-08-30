"""工具层单元测试：全程不调用任何模型 API（mock 自由、免 key）。"""

import sys
import urllib.error
from unittest import mock

from agent.tools import TOOLS, dispatch, tool_schemas
from agent.tools.shell_tools import _decode, is_dangerous


def test_seven_tools_registered():
    names = {t.name for t in TOOLS}
    assert names == {
        "read_file",
        "write_file",
        "edit_file",
        "execute_command",
        "list_directory",
        "search_content",
        "web_search",
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


def test_decode_fallback():
    assert _decode("中文".encode("utf-8")) == "中文"  # UTF-8 优先
    assert _decode("中文".encode("gbk")) == "中文"  # 回退 GBK（Windows 控制台代码页）
    assert _decode("中文".encode("gbk"), ["latin-1"]) != "中文"  # 显式编码列表优先
    out = _decode(b"\xff\xfe\x80")  # 全部失败 → 容错替换
    assert "\ufffd" in out


def test_execute_command_decodes_cmd_codepage_output(tmp_path):
    """模拟 cmd 控制台代码页（GBK）字节输出，应回退解码而非乱码。"""
    cmd = (
        f'"{sys.executable}" -c '
        + '"import sys; sys.stdout.buffer.write(\'中文GBK\'.encode(\'gbk\'))"'
    )
    out = dispatch("execute_command", {"command": cmd, "timeout": 15}, str(tmp_path))
    assert "中文GBK" in out  # GBK 回退解码还原，无乱码


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


# ---------- web_search（迭代 8 · 8.0） ----------

_SAMPLE_DDG_HTML = """<html><body>
<div class="result">
  <a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage&amp;rut=abc">示例标题</a>
  <a class="result__snippet" href="https://example.com/page">这是摘要内容</a>
</div>
<div class="result">
  <a class="result__a" href="https://example.org/x">第二个结果</a>
  <a class="result__snippet">第二段摘要</a>
</div>
</body></html>"""


def _fake_urlopen(html: str):
    resp = mock.Mock()
    resp.read.return_value = html.encode("utf-8")
    resp.__enter__ = mock.Mock(return_value=resp)
    resp.__exit__ = mock.Mock(return_value=False)
    return resp


def test_web_search_parses_results(tmp_path):
    with mock.patch(
        "agent.tools.search_tools.urllib.request.urlopen",
        return_value=_fake_urlopen(_SAMPLE_DDG_HTML),
    ):
        out = dispatch("web_search", {"query": "测试"}, str(tmp_path))
    assert "[1] 示例标题" in out
    assert "example.com/page" in out  # uddg 跳转还原
    assert "这是摘要内容" in out
    assert "[2] 第二个结果" in out


def test_web_search_requires_query(tmp_path):
    out = dispatch("web_search", {}, str(tmp_path))
    assert "缺少 query" in out


def test_web_search_request_error(tmp_path):
    with mock.patch(
        "agent.tools.search_tools.urllib.request.urlopen",
        side_effect=urllib.error.URLError("boom"),
    ):
        out = dispatch("web_search", {"query": "x"}, str(tmp_path))
    assert "搜索请求失败" in out


def test_web_search_clamps_max_results(tmp_path):
    with mock.patch(
        "agent.tools.search_tools.urllib.request.urlopen",
        return_value=_fake_urlopen(_SAMPLE_DDG_HTML),
    ):
        out = dispatch("web_search", {"query": "x", "max_results": 1}, str(tmp_path))
    assert "[1] 示例标题" in out and "[2]" not in out
    with mock.patch(
        "agent.tools.search_tools.urllib.request.urlopen",
        return_value=_fake_urlopen(_SAMPLE_DDG_HTML),
    ):
        out = dispatch("web_search", {"query": "x", "max_results": 99}, str(tmp_path))
    assert "[2] 第二个结果" in out  # 钳制到 10，样本 2 条


def test_web_search_uses_env_template(monkeypatch, tmp_path):
    monkeypatch.setenv("SEARCH_API_URL", "https://mysearch.test/?q={query}")
    called = {}

    def fake(req, timeout):
        called["url"] = req.full_url
        return _fake_urlopen("<html></html>")

    with mock.patch("agent.tools.search_tools.urllib.request.urlopen", side_effect=fake):
        out = dispatch("web_search", {"query": "你好 世界"}, str(tmp_path))
    assert called["url"] == "https://mysearch.test/?q=%E4%BD%A0%E5%A5%BD+%E4%B8%96%E7%95%8C"
    assert "未找到" in out


def test_web_search_empty_results(tmp_path):
    with mock.patch(
        "agent.tools.search_tools.urllib.request.urlopen",
        return_value=_fake_urlopen("<html></html>"),
    ):
        out = dispatch("web_search", {"query": "xyz"}, str(tmp_path))
    assert "未找到" in out


def test_web_search_parses_lite_layout(tmp_path):
    """lite 端点结构：result-link 锚点 + result-snippet td。"""
    lite_html = """<html><body>
<a rel="nofollow" href="https://lite.example.com/a" class='result-link'>Lite 标题</a>
<td class='result-snippet'>Lite 摘要文本</td>
</body></html>"""
    with mock.patch(
        "agent.tools.search_tools.urllib.request.urlopen",
        return_value=_fake_urlopen(lite_html),
    ):
        out = dispatch("web_search", {"query": "lite"}, str(tmp_path))
    assert "[1] Lite 标题" in out
    assert "lite.example.com/a" in out
    assert "Lite 摘要文本" in out
