"""极简 Web 界面：自写标准库 HTTP 服务（不引入 Web 框架，零新依赖）。

入口：python -m agent.web [--host 127.0.0.1] [--port 8080] [--workdir .]
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import queue
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .config import Config
from .llm import LLMClient
from .loop import run

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>编程智能体</title>
<style>
  body { font-family: Consolas, monospace; margin: 2rem; background: #101418; color: #d8dee9; }
  input { width: 72%; padding: .5rem; background: #1c2128; color: #d8dee9; border: 1px solid #333; }
  button { padding: .5rem 1.2rem; cursor: pointer; background: #2e7d32; color: #fff; border: none; }
  pre { white-space: pre-wrap; background: #000; padding: 1rem; min-height: 22rem; border: 1px solid #333; }
</style>
</head>
<body>
<h2>编程智能体（Coding Agent）</h2>
<input id="task" placeholder="输入编程任务，如：创建 hello.py 打印 Hello 并运行">
<button onclick="run()">运行</button>
<pre id="out">等待任务…</pre>
<script>
function run() {
  const task = document.getElementById('task').value;
  const out = document.getElementById('out');
  out.textContent = '运行中…\\n';
  const es = new EventSource('/events?task=' + encodeURIComponent(task));
  es.onmessage = function (e) {
    if (e.data === '[DONE]') { es.close(); return; }
    out.textContent += JSON.parse(e.data).text;
  };
  es.onerror = function () { es.close(); };
}
</script>
</body>
</html>
"""


def run_task_output(config: Config, task: str, workdir: str = ".") -> str:
    """运行任务并捕获全部 stdout（过程日志 + 最终答复）。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        client = LLMClient(config)
        result = run(config, task, workdir=workdir, client=client)
        if not config.stream:
            print(result)
    return buf.getvalue()


class _SseWriter:
    """把 stdout 写入转发到队列，供 SSE 流式发送。"""

    def __init__(self, q: queue.Queue):
        self._q = q

    def write(self, text: str) -> int:
        if text:
            self._q.put(text)
        return len(text)

    def flush(self) -> None:
        pass


class AgentHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler 约定命名
        if self.path == "/":
            data = INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/events"):
            self._handle_events()
        else:
            self.send_error(404)

    def _handle_events(self) -> None:
        """SSE 流式：后台线程运行 agent，逐条推送输出，[DONE] 结束。"""
        parsed = urllib.parse.urlparse(self.path)
        task = (urllib.parse.parse_qs(parsed.query).get("task") or [""])[0].strip()
        if not task:
            self.send_error(400, "缺少 task 参数")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        q: queue.Queue = queue.Queue()
        writer = _SseWriter(q)
        config = self.server.config
        workdir = self.server.workdir

        def worker() -> None:
            try:
                with contextlib.redirect_stdout(writer):
                    client = LLMClient(config)
                    result = run(config, task, workdir=workdir, client=client)
                    if not config.stream:
                        print(result)
            except Exception as exc:  # noqa: BLE001 - 错误推送给前端
                print(f"错误：{exc}")
            finally:
                q.put(None)  # 结束哨兵

        threading.Thread(target=worker, daemon=True).start()
        try:
            while True:
                item = q.get()
                if item is None:
                    break
                payload = json.dumps({"text": item}, ensure_ascii=False)
                self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def do_POST(self):  # noqa: N802
        if self.path == "/run":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                task = str(body.get("task", "")).strip()
                if not task:
                    raise ValueError("任务为空")
                output = run_task_output(self.server.config, task, self.server.workdir)
                result = {"ok": True, "output": output}
            except Exception as exc:  # noqa: BLE001 - 错误回传前端展示
                result = {"ok": False, "error": str(exc)}
            data = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def log_message(self, format, *args):  # noqa: A002 - 静默访问日志
        pass


def serve(config: Config, workdir: str = ".", host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), AgentHandler)
    server.config = config
    server.workdir = workdir
    print(f"Web 界面已启动：http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent.web", description="编程智能体 Web 界面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--workdir", default=".")
    args = parser.parse_args(argv)
    config = Config.from_env()
    serve(config, workdir=args.workdir, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
