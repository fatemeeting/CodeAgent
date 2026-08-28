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
from pathlib import Path

from .config import Config
from .llm import LLMClient
from .loop import run

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>编程智能体 · Coding Agent</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: #0f1115; color: #d8dee9; height: 100vh; display: flex; flex-direction: column; }
  header { display: flex; align-items: center; gap: .8rem; padding: .6rem 1rem; background: #161a21; border-bottom: 1px solid #232a35; }
  header h1 { font-size: .95rem; margin: 0; font-weight: 600; white-space: nowrap; }
  .ws { flex: 1; display: flex; gap: .4rem; }
  .ws input { flex: 1; width: 100%; padding: .4rem .6rem; background: #0f1115; color: #d8dee9; border: 1px solid #2c3440; border-radius: 4px; font-size: .85rem; }
  .ws .pick { padding: 0 .8rem; background: #1c2128; color: #d8dee9; border: 1px solid #2c3440; border-radius: 4px; cursor: pointer; font-size: .85rem; white-space: nowrap; }
  #chat { flex: 1; overflow-y: auto; padding: 1rem 1.2rem; }
  .tip { color: #8b949e; font-size: .82rem; }
  .msg { display: flex; margin-bottom: .9rem; }
  .msg.user { justify-content: flex-end; }
  .bubble { max-width: 80%; padding: .55rem .85rem; border-radius: 10px; white-space: pre-wrap; word-break: break-word; font-size: .9rem; line-height: 1.55; }
  .msg.user .bubble { background: #1f4d2e; border: 1px solid #2e7d32; }
  .msg.agent .bubble { background: #161a21; border: 1px solid #232a35; font-family: Consolas, "Courier New", monospace; }
  .tool { color: #58a6ff; }
  .obs { color: #7ee787; }
  footer { display: flex; gap: .5rem; padding: .7rem 1rem; background: #161a21; border-top: 1px solid #232a35; }
  footer textarea { flex: 1; resize: none; height: 46px; padding: .5rem .6rem; background: #0f1115; color: #d8dee9; border: 1px solid #2c3440; border-radius: 6px; font-size: .9rem; font-family: inherit; }
  footer button { padding: 0 1.3rem; background: #2e7d32; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; }
</style>
</head>
<body>
<header>
  <h1>🤖 编程智能体</h1>
  <div class="ws">
    <input id="ws" placeholder="工作区目录（先指定，如 E:\\demo，留空用默认）">
    <button class="pick" onclick="pickWs()" title="唤起系统文件夹选择器">📂 选择</button>
  </div>
</header>
<div id="chat"><div class="tip">先指定上方工作区，再发送任务；agent 将在该工作区内完成项目。</div></div>
<footer>
  <textarea id="task" placeholder="输入编程任务，Enter 发送（Shift+Enter 换行）"></textarea>
  <button onclick="send()">发送</button>
</footer>
<script>
const chat = document.getElementById('chat');
function addMsg(role) {
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + role;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble._raw = '';
  wrap.appendChild(bubble);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return bubble;
}
function render(bubble) {
  bubble.innerHTML = '';
  bubble._raw.split('\\n').forEach(function (line, i) {
    if (i > 0) bubble.appendChild(document.createElement('br'));
    let node;
    if (line.indexOf('[步骤') === 0) { node = document.createElement('span'); node.className = 'tool'; }
    else if (line.indexOf('        ↳') === 0) { node = document.createElement('span'); node.className = 'obs'; }
    else { node = document.createElement('span'); }
    node.textContent = line;
    bubble.appendChild(node);
  });
}
async function pickWs() {
  try {
    const resp = await fetch('/pick-workspace', {method: 'POST'});
    const data = await resp.json();
    if (data.ok) { document.getElementById('ws').value = data.path; }
    else if (data.error) { alert(data.error); }
  } catch (e) { alert('请求失败：' + e); }
}
function send() {
  const taskEl = document.getElementById('task');
  const task = taskEl.value.trim();
  if (!task) return;
  const ws = document.getElementById('ws').value.trim();
  taskEl.value = '';
  const ub = addMsg('user'); ub._raw = task; render(ub);
  const ab = addMsg('agent');
  const es = new EventSource('/events?task=' + encodeURIComponent(task) + '&workdir=' + encodeURIComponent(ws));
  es.onmessage = function (e) {
    if (e.data === '[DONE]') { es.close(); ab._raw += '\\n✓ 完成'; render(ab); return; }
    ab._raw += JSON.parse(e.data).text;
    render(ab);
    chat.scrollTop = chat.scrollHeight;
  };
  es.onerror = function () { es.close(); };
}
document.getElementById('task').addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});
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


def pick_workspace() -> str | None:
    """唤起系统原生文件夹选择器（tkinter 标准库）；失败或无选择返回 None。"""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askdirectory(title="选择工作区根目录")
        root.destroy()
        return path or None
    except Exception:  # noqa: BLE001 - 无图形环境时优雅降级
        return None


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
        query = urllib.parse.parse_qs(parsed.query)
        task = (query.get("task") or [""])[0].strip()
        if not task:
            self.send_error(400, "缺少 task 参数")
            return
        workdir = (query.get("workdir") or [None])[0] or self.server.workdir
        if not Path(workdir).is_dir():
            self.send_error(400, f"工作区不存在：{workdir}")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        q: queue.Queue = queue.Queue()
        writer = _SseWriter(q)
        config = self.server.config

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
                workdir = str(body.get("workdir") or self.server.workdir)
                if not Path(workdir).is_dir():
                    raise ValueError(f"工作区不存在：{workdir}")
                output = run_task_output(self.server.config, task, workdir)
                result = {"ok": True, "output": output}
            except Exception as exc:  # noqa: BLE001 - 错误回传前端展示
                result = {"ok": False, "error": str(exc)}
            data = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/pick-workspace":
            try:
                path = pick_workspace()
                result = (
                    {"ok": True, "path": path}
                    if path
                    else {"ok": False, "path": None, "error": "未选择目录或无法唤起系统对话框（可手动输入）"}
                )
            except Exception as exc:  # noqa: BLE001
                result = {"ok": False, "path": None, "error": str(exc)}
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
