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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>编程智能体 · Coding Agent</title>
<style>
  :root {
    --bg: #f7f7f4; --surface: #ffffff; --border: #e5e4df;
    --text: #26251e; --muted: #8a887e; --accent: #f54e00;
    --accent-hover: #d94400; --code-bg: #fbfaf8; --ok: #2e7d32; --err: #c62828;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
  /* 工作区管理器（欢迎页整页 + 弹层复用同一卡片） */
  #welcome { flex: 1; display: flex; align-items: center; justify-content: center; padding: 24px; }
  .mgr-card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 40px 44px; width: 520px; max-width: 92vw; box-shadow: 0 2px 12px rgba(38,37,30,.06); display: flex; flex-direction: column; gap: 12px; }
  .mgr-title { font-size: 26px; font-weight: 700; text-align: center; letter-spacing: -.5px; }
  .mgr-sub { color: var(--muted); text-align: center; margin-bottom: 8px; }
  .btn { border: 1px solid var(--border); background: var(--surface); color: var(--text); border-radius: 8px; padding: 10px 14px; cursor: pointer; font-size: 14px; }
  .btn:hover { background: var(--code-bg); }
  .btn-accent { background: var(--accent); color: #fff; border: none; font-weight: 600; }
  .btn-accent:disabled { background: #e3cfc4; cursor: not-allowed; }
  .btn-accent:not(:disabled):hover { background: var(--accent-hover); }
  .mgr-divider { height: 1px; background: var(--border); margin: 4px 0; }
  .mgr-path { padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; font-family: Consolas, monospace; width: 100%; }
  .mgr-status { font-size: 13px; min-height: 18px; color: var(--muted); }
  .mgr-status.ok { color: var(--ok); }
  .mgr-status.err { color: var(--err); }
  .mgr-recents-title { font-size: 13px; color: var(--muted); }
  .recent { padding: 8px 10px; border-radius: 8px; cursor: pointer; font-family: Consolas, monospace; font-size: 13px; display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  .recent:hover { background: var(--code-bg); }
  .recent .path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
  .recent .del { color: var(--muted); font-weight: 700; padding: 0 4px; flex-shrink: 0; }
  .recent .del:hover { color: var(--err); }
  .mgr-cancel { border: none; background: none; color: var(--muted); cursor: pointer; font-size: 13px; padding: 6px; }
  /* 主布局骨架 */
  #main { display: none; flex: 1; flex-direction: column; }
  #topbar { display: flex; align-items: center; gap: 12px; padding: 8px 16px; background: var(--surface); border-bottom: 1px solid var(--border); }
  .brand { font-weight: 700; font-size: 14px; letter-spacing: -.3px; }
  .mode-switch { display: flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  .mode-switch button { padding: 7px 16px; border: none; background: var(--surface); cursor: pointer; font-size: 13px; color: var(--muted); }
  .mode-switch button.active { background: var(--accent); color: #fff; font-weight: 600; }
  .ws-chip { margin-left: auto; display: flex; align-items: center; gap: 8px; font-family: Consolas, monospace; font-size: 13px; border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; background: var(--code-bg); }
  .ws-chip button { border: none; background: none; cursor: pointer; color: var(--accent); font-size: 13px; font-weight: 600; }
  #content { flex: 1; display: flex; min-height: 0; }
  .pane { padding: 16px; overflow: auto; }
  #pane-left { width: 42%; border-right: 1px solid var(--border); }
  #pane-right { flex: 1; }
  .placeholder { color: var(--muted); font-size: 14px; display: flex; align-items: center; justify-content: center; height: 100%; border: 1px dashed var(--border); border-radius: 12px; }
  /* 弹层 */
  #modal { display: none; position: fixed; inset: 0; background: rgba(38,37,30,.45); align-items: center; justify-content: center; z-index: 10; padding: 24px; }
  #modal .mgr-card { box-shadow: 0 8px 40px rgba(38,37,30,.2); }
</style>
</head>
<body>
<div id="welcome"></div>
<div id="main">
  <div id="topbar">
    <span class="brand">🤖 编程智能体</span>
    <div class="mode-switch">
      <button id="mode-agent" class="active" onclick="setMode('agent')">Agent Window</button>
      <button id="mode-editor" onclick="setMode('editor')">Editor Window</button>
    </div>
    <div class="ws-chip">
      <span id="ws-name"></span>
      <button onclick="openManager()" title="切换工作区">🔄 切换</button>
    </div>
  </div>
  <div id="content">
    <div id="pane-left" class="pane"><div class="placeholder">对话区（切片 6.7）</div></div>
    <div id="pane-right" class="pane"><div class="placeholder">代码文件页（切片 6.7）</div></div>
  </div>
</div>
<div id="modal"><div id="modal-card"></div></div>
<script>
const state = {
  workspace: localStorage.getItem('agent.workspace') || '',
  recents: JSON.parse(localStorage.getItem('agent.recents') || '[]'),
};
let activeManager = null;
let validateTimer = null;

function mgr(sel) { return activeManager ? activeManager.querySelector(sel) : null; }

function buildManager(container) {
  const isModal = container.id === 'modal-card';
  activeManager = container;
  container.innerHTML = `
    <div class="mgr-card">
      <div class="mgr-title">🤖 编程智能体</div>
      <div class="mgr-sub">选择 AI 助手的工作区目录</div>
      <button class="btn" onclick="pickWs()">📂 选择文件夹</button>
      <div class="mgr-divider"></div>
      <input class="mgr-path" id="mgr-path" placeholder="或手动输入路径，如 E:/demo">
      <div class="mgr-status" id="mgr-status"></div>
      <div class="mgr-divider"></div>
      <div class="mgr-recents-title">最近使用</div>
      <div id="mgr-recents"></div>
      <div class="mgr-divider"></div>
      <button class="btn-accent" id="mgr-confirm" disabled>✓ 确认并进入工作区</button>
      ${isModal ? '<button class="mgr-cancel" onclick="closeManager()">取消</button>' : ''}
    </div>`;
  const input = mgr('#mgr-path');
  input.addEventListener('input', scheduleValidate);
  mgr('#mgr-confirm').addEventListener('click', confirmWorkspace);
  refreshRecents();
  if (state.workspace) { input.value = state.workspace; scheduleValidate(); }
}

async function pickWs() {
  try {
    const resp = await fetch('/pick-workspace', {method: 'POST'});
    const data = await resp.json();
    if (data.ok) { mgr('#mgr-path').value = data.path; scheduleValidate(); }
    else if (data.error) { setStatus(data.error, false); }
  } catch (e) { setStatus('请求失败：' + e, false); }
}

function setStatus(text, ok) {
  const s = mgr('#mgr-status');
  if (!s) return;
  s.textContent = text;
  s.className = 'mgr-status' + (ok ? ' ok' : ' err');
}

function scheduleValidate() { clearTimeout(validateTimer); validateTimer = setTimeout(validate, 400); }

async function validate() {
  const path = mgr('#mgr-path').value.trim();
  const confirm = mgr('#mgr-confirm');
  if (!path) { setStatus('', false); confirm.disabled = true; return; }
  setStatus('校验中…', false);
  try {
    const resp = await fetch('/tree?workdir=' + encodeURIComponent(path));
    const data = await resp.json();
    if (data.ok) { setStatus('✓ 目录存在，可进入', true); confirm.disabled = false; }
    else { setStatus('✗ ' + (data.error || '目录不存在'), false); confirm.disabled = true; }
  } catch (e) { setStatus('✗ 校验失败：' + e, false); confirm.disabled = true; }
}

function confirmWorkspace() {
  const path = mgr('#mgr-path').value.trim();
  state.workspace = path;
  state.recents = [path, ...state.recents.filter(r => r !== path)].slice(0, 8);
  localStorage.setItem('agent.workspace', path);
  localStorage.setItem('agent.recents', JSON.stringify(state.recents));
  enterMain();
}

function refreshRecents() {
  const box = mgr('#mgr-recents');
  if (!box) return;
  if (!state.recents.length) { box.innerHTML = '<div class="mgr-status">暂无记录</div>'; return; }
  box.innerHTML = '';
  state.recents.forEach(path => {
    const row = document.createElement('div');
    row.className = 'recent';
    const span = document.createElement('span');
    span.className = 'path';
    span.textContent = path;
    span.onclick = () => { mgr('#mgr-path').value = path; scheduleValidate(); };
    const del = document.createElement('span');
    del.className = 'del';
    del.textContent = '✕';
    del.onclick = () => {
      state.recents = state.recents.filter(r => r !== path);
      localStorage.setItem('agent.recents', JSON.stringify(state.recents));
      refreshRecents();
    };
    row.appendChild(span); row.appendChild(del);
    box.appendChild(row);
  });
}

function enterMain() {
  document.getElementById('welcome').style.display = 'none';
  document.getElementById('main').style.display = 'flex';
  document.getElementById('ws-name').textContent = state.workspace;
  closeManager();
}

function openManager() {
  document.getElementById('modal').style.display = 'flex';
  buildManager(document.getElementById('modal-card'));
}

function closeManager() {
  document.getElementById('modal').style.display = 'none';
  activeManager = document.getElementById('welcome');
}

function setMode(mode) {
  document.getElementById('mode-agent').classList.toggle('active', mode === 'agent');
  document.getElementById('mode-editor').classList.toggle('active', mode === 'editor');
  document.getElementById('pane-left').innerHTML = mode === 'agent'
    ? '<div class="placeholder">对话区（切片 6.7）</div>'
    : '<div class="placeholder">文件树（切片 6.8）</div>';
}

(async function boot() {
  buildManager(document.getElementById('welcome'));
  if (state.workspace) {
    try {
      const resp = await fetch('/tree?workdir=' + encodeURIComponent(state.workspace));
      const data = await resp.json();
      if (data.ok) { enterMain(); }
    } catch (e) { /* 校验失败留在欢迎页 */ }
  }
})();
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


_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".idea", ".vscode", "dist", "build"}


def _workspace_tree(workdir: str) -> list[dict]:
    """工作区顶层条目（目录 / 文件），用于工作区校验与文件树。"""
    root = Path(workdir)
    if not root.is_dir():
        raise ValueError(f"工作区不存在：{workdir}")
    entries = []
    for p in sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        if p.name.startswith(".") or p.name in _SKIP_DIRS:
            continue
        entries.append({"name": p.name, "type": "dir" if p.is_dir() else "file"})
    return entries


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
        elif self.path.startswith("/tree"):
            self._handle_tree()
        else:
            self.send_error(404)

    def _handle_tree(self) -> None:
        """工作区校验 + 顶层文件树。"""
        parsed = urllib.parse.urlparse(self.path)
        workdir = (urllib.parse.parse_qs(parsed.query).get("workdir") or [None])[0] or self.server.workdir
        try:
            tree = _workspace_tree(workdir)
            result = {"ok": True, "workdir": workdir, "tree": tree}
        except Exception as exc:  # noqa: BLE001
            result = {"ok": False, "error": str(exc)}
        data = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

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
