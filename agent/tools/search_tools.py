"""网络搜索工具：web_search（标准库 urllib + html.parser，零新依赖）。

默认 DuckDuckGo lite 接口（无需 API key，结构稳定）。可通过环境变量接入自定义搜索 API：
- SEARCH_API_URL：URL 模板，{query} 为查询占位符（返回 DuckDuckGo 结构 HTML 时直接解析）
- SEARCH_API_KEY：可选 key（仅用于自定义 API 的 Authorization: Bearer 头）
"""

from __future__ import annotations

import os
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from .base import Tool

MAX_RESULTS = 10
TIMEOUT_SECONDS = 15
SNIPPET_CHARS = 200

_DDG_URL = "https://lite.duckduckgo.com/lite/?q={query}"


def _search_url(query: str) -> str:
    template = os.environ.get("SEARCH_API_URL", "").strip()
    if template:
        return template.replace("{query}", urllib.parse.quote_plus(query))
    return _DDG_URL.replace("{query}", urllib.parse.quote_plus(query))


def _decode_url(link: str) -> str:
    """DDG 结果链接形如 //duckduckgo.com/l/?uddg=<url>&rut=...，解出真实 URL。"""
    if "uddg=" in link:
        parsed = urllib.parse.urlparse(link)
        qs = urllib.parse.parse_qs(parsed.query)
        target = (qs.get("uddg") or [""])[0]
        if target:
            return target
    return link


class _DdgParser(HTMLParser):
    """按 DuckDuckGo HTML 结构收集 标题/URL/摘要。

    兼容两种结构：html 端点（class=result__a / result__snippet）与
    lite 端点（class=result-link / result-snippet，摘要为 td 元素）。
    """

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._pending: dict[str, str] | None = None
        self._mode: str | None = None  # None | "title" | "snippet"

    def _flush(self) -> None:
        if self._pending and (self._pending["title"].strip() or self._pending["url"]):
            self.results.append(self._pending)
        self._pending = None
        self._mode = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs = dict(attrs)
        cls = attrs.get("class") or ""
        if "result__a" in cls or "result-link" in cls:
            self._flush()
            self._pending = {
                "title": "",
                "url": _decode_url(attrs.get("href", "")),
                "snippet": "",
            }
            self._mode = "title"
        elif "result__snippet" in cls or "result-snippet" in cls:
            self._mode = "snippet"

    def handle_data(self, data: str) -> None:
        if self._pending is None:
            return
        if self._mode == "title":
            self._pending["title"] += data
        elif self._mode == "snippet":
            self._pending["snippet"] += data

    def close(self) -> None:
        self._flush()
        super().close()


def _web_search(arguments: dict, workdir: str) -> str:
    query = str(arguments.get("query") or "").strip()
    if not query:
        return "错误：缺少 query"
    max_results = int(arguments.get("max_results", 5))
    max_results = max(1, min(max_results, MAX_RESULTS))

    url = _search_url(query)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CodingAgent/0.8)"})
    api_key = os.environ.get("SEARCH_API_KEY", "").strip()
    if api_key:
        req.add_header("Authorization", "Bearer " + api_key)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read()
    except urllib.error.URLError as exc:
        return f"错误：搜索请求失败：{exc}"
    except Exception as exc:  # noqa: BLE001 - 超时/网络异常统一回填
        return f"错误：搜索超时或网络异常：{exc}"

    text = raw.decode("utf-8", errors="replace")
    parser = _DdgParser()
    parser.feed(text)
    parser.close()
    if not parser.results:
        return "（未找到搜索结果）"

    lines = []
    for i, r in enumerate(parser.results[:max_results], 1):
        title = " ".join(r["title"].split()).strip() or "(无标题)"
        snippet = " ".join(r["snippet"].split()).strip()
        if len(snippet) > SNIPPET_CHARS:
            snippet = snippet[:SNIPPET_CHARS] + "…"
        lines.append(f"[{i}] {title}\n    {r['url']}\n    {snippet}")
    return "\n".join(lines)


WEB_SEARCH = Tool(
    name="web_search",
    description="搜索互联网获取最新信息（默认 DuckDuckGo，无需 key）。返回标题/URL/摘要列表。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "max_results": {"type": "integer", "description": "返回条数（1-10，默认 5）"},
        },
        "required": ["query"],
    },
    handler=_web_search,
)
