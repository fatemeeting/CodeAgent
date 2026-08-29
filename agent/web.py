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
from .tools.shell_tools import execute_command, is_dangerous

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
  .ws-chip { margin-left: auto; display: flex; align-items: center; gap: 8px; font-family: Consolas, monospace; font-size: 13px; border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; background: var(--code-bg); }
  .ws-chip button { border: none; background: none; cursor: pointer; color: var(--accent); font-size: 13px; font-weight: 600; }
  #content { flex: 1; display: flex; min-height: 0; }
  .pane { display: flex; flex-direction: column; overflow: hidden; }
  #pane-left { width: 18%; border-right: 1px solid var(--border); }
  #pane-center { flex: 1; }
  #pane-right { width: 30%; border-left: 1px solid var(--border); }
  #terminal-panel { display: flex; flex-direction: column; height: 180px; border-top: 1px solid var(--border); background: var(--surface); }
  #editor-host { flex: 1; min-height: 0; }
  .placeholder { color: var(--muted); font-size: 14px; display: flex; align-items: center; justify-content: center; height: 100%; border: 1px dashed var(--border); border-radius: 12px; margin: 16px; }
  /* 对话区（右侧聊天面板） */
  #chat-history { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
  #chat-inputbar { display: flex; gap: 8px; padding: 12px 16px; background: var(--surface); border-top: 1px solid var(--border); }
  #chat-input { flex: 1; resize: none; height: 44px; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; font-family: inherit; background: var(--bg); color: var(--text); }
  .msg { display: flex; }
  .msg.user { justify-content: flex-end; }
  .bubble { max-width: 85%; padding: 8px 12px; border-radius: 12px; white-space: pre-wrap; word-break: break-word; font-size: 13px; line-height: 1.55; }
  .msg.user .bubble { background: var(--accent); color: #fff; }
  .msg.agent .bubble { background: var(--surface); border: 1px solid var(--border); font-family: Consolas, "Courier New", monospace; }
  .tool { color: #b33a00; font-weight: 600; }
  .obs { color: var(--ok); }
  .bubble pre { background: var(--code-bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px; margin: 4px 0; overflow-x: auto; }
  .bubble code.ic { background: var(--code-bg); border: 1px solid var(--border); border-radius: 4px; padding: 0 4px; font-size: 12px; }
  .bubble h1, .bubble h2, .bubble h3, .bubble h4 { margin: 6px 0 2px; font-size: 1.02em; }
  .bubble ul { margin: 2px 0; padding-left: 18px; }
  .bubble a { color: var(--accent); }
  /* 文件页（右栏） */
  #file-header { display: flex; justify-content: flex-end; align-items: center; gap: 8px; padding: 12px 16px 8px; }
  #file-tab { display: none; font-family: Consolas, monospace; font-size: 13px; font-weight: 600; background: var(--surface); border: 1px solid var(--border); border-radius: 6px 6px 0 0; padding: 6px 12px; }
  #file-view, .file-view { flex: 1; margin: 0 16px 16px; background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; padding: 12px; overflow: auto; font-family: Consolas, monospace; font-size: 13px; line-height: 1.5; }
  #file-view .ln, .file-view .ln { display: inline-block; width: 40px; color: var(--muted); text-align: right; margin-right: 12px; user-select: none; }
  /* 文件树（Editor 左栏） */
  .tree-title { font-size: 12px; font-weight: 700; color: var(--muted); padding: 10px 16px 6px; letter-spacing: .3px; }
  #tree-root { flex: 1; overflow: auto; padding: 4px 8px 16px; }
  .tree-node { font-size: 13px; }
  .tree-label { display: block; padding: 3px 6px; border-radius: 6px; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .tree-label:hover { background: var(--code-bg); }
  .tree-label.file { font-family: Consolas, monospace; }
  .tree-kids { padding-left: 14px; }
  /* 终端（Editor 底部） */
  #term-header { display: flex; justify-content: space-between; align-items: center; padding: 6px 16px; font-size: 12px; font-weight: 700; color: var(--muted); border-bottom: 1px solid var(--border); }
  #term-toggle { cursor: pointer; color: var(--accent); font-weight: 600; }
  #term-body { flex: 1; display: flex; flex-direction: column; min-height: 0; }
  #term-output { flex: 1; overflow: auto; padding: 8px 16px; font-family: Consolas, monospace; font-size: 12.5px; background: #1e1b16; color: #e8e4da; }
  #term-output .term-warn { color: #ffb020; }
  #term-output .term-err { color: #ff7a6e; }
  #term-inputbar { display: flex; gap: 8px; padding: 6px 16px; border-top: 1px solid var(--border); align-items: center; }
  #term-prompt { color: var(--accent); font-family: Consolas, monospace; font-weight: 700; }
  #term-input { flex: 1; border: none; background: none; outline: none; font-family: Consolas, monospace; font-size: 13px; color: var(--text); }
  /* 弹层 */
  #modal { display: none; position: fixed; inset: 0; background: rgba(38,37,30,.45); align-items: center; justify-content: center; z-index: 10; padding: 24px; }
  #modal .mgr-card { box-shadow: 0 8px 40px rgba(38,37,30,.2); }
</style>
<script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs/loader.js"></script>
<script>
  if (window.require) {
    require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs' } });
    require(['vs/editor/editor.main'], function () { window.monacoReady = true; });
  }
</script>
</head>
<body>
<div id="welcome"></div>
<div id="main">
  <div id="topbar">
    <span class="brand">🤖 编程智能体</span>
    <div class="ws-chip">
      <span id="ws-name"></span>
      <button onclick="openManager()" title="切换工作区">🔄 切换</button>
    </div>
  </div>
  <div id="content">
    <div id="pane-left" class="pane"></div>
    <div id="pane-center" class="pane"></div>
    <div id="pane-right" class="pane"></div>
  </div>
  <div id="terminal-panel"></div>
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
  buildLayout();
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

let chatMessages = [];
let editor = null;

function buildLayout() {
  buildFileTree();
  buildEditor();
  buildChat('pane-right');
  buildTerminal();
}

/* ---------- 对话（Agent 左栏 / Editor 右栏复用；状态存 chatMessages 重放） ---------- */
function buildChat(containerId) {
  document.getElementById(containerId).innerHTML = `
    <div id="chat-history"></div>
    <div id="chat-inputbar">
      <textarea id="chat-input" placeholder="输入编程任务，Enter 发送（Shift+Enter 换行）"></textarea>
      <button class="btn-accent" onclick="sendTask()">发送</button>
    </div>`;
  chatMessages.forEach(m => appendMsg(m.role, m.raw));
  const h = document.getElementById('chat-history');
  h.scrollTop = h.scrollHeight;
  document.getElementById('chat-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendTask(); }
  });
}

function appendMsg(role, raw) {
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + role;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble._raw = raw;
  wrap.appendChild(bubble);
  document.getElementById('chat-history').appendChild(wrap);
  renderBubble(bubble);
  const h = document.getElementById('chat-history');
  h.scrollTop = h.scrollHeight;
  return bubble;
}

function renderBubble(bubble) {
  bubble.innerHTML = '';
  const lines = bubble._raw.split('\\n');
  let md = [];
  const flush = () => {
    if (md.length) { bubble.appendChild(renderMarkdown(md.join('\\n'))); md = []; }
  };
  lines.forEach(line => {
    if (line.indexOf('[步骤') === 0 || line.indexOf('        ↳') === 0) {
      flush();
      const div = document.createElement('div');
      const span = document.createElement('span');
      span.className = line.indexOf('[步骤') === 0 ? 'tool' : 'obs';
      span.textContent = line;
      div.appendChild(span);
      bubble.appendChild(div);
    } else {
      md.push(line);
    }
  });
  flush();
}

/* 零依赖迷你 Markdown 渲染：代码块 / 行内代码 / 粗体 / 标题 / 列表（textContent 构建，防 XSS） */
function inlineNodes(text) {
  const frag = document.createDocumentFragment();
  let s = text;
  while (s) {
    const b = s.indexOf('**');
    const c = s.indexOf('`');
    if (b === -1 && c === -1) { frag.appendChild(document.createTextNode(s)); break; }
    let pos, kind;
    if (b !== -1 && (c === -1 || b < c)) { pos = b; kind = 'bold'; }
    else { pos = c; kind = 'code'; }
    if (pos > 0) frag.appendChild(document.createTextNode(s.slice(0, pos)));
    const endTok = kind === 'bold' ? '**' : '`';
    const end = s.indexOf(endTok, pos + endTok.length);
    if (end === -1) { frag.appendChild(document.createTextNode(s.slice(pos))); break; }
    const node = kind === 'bold' ? document.createElement('strong') : document.createElement('code');
    if (kind === 'code') node.className = 'ic';
    node.textContent = s.slice(pos + endTok.length, end);
    frag.appendChild(node);
    s = s.slice(end + endTok.length);
  }
  return frag;
}

function renderMarkdown(text) {
  const frag = document.createDocumentFragment();
  const lines = text.split('\\n');
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith('```')) {
      const buf = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) { buf.push(lines[i]); i++; }
      i++;
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      code.textContent = buf.join('\\n');
      pre.appendChild(code);
      frag.appendChild(pre);
      continue;
    }
    const h = line.match(/^(#{1,4})\\s+(.*)$/);
    if (h) {
      const el = document.createElement('h' + h[1].length);
      el.appendChild(inlineNodes(h[2]));
      frag.appendChild(el);
      i++;
      continue;
    }
    const li = line.match(/^\\s*[-*]\\s+(.*)$/);
    if (li) {
      const ul = document.createElement('ul');
      while (i < lines.length) {
        const m2 = lines[i].match(/^\\s*[-*]\\s+(.*)$/);
        if (!m2) break;
        const item = document.createElement('li');
        item.appendChild(inlineNodes(m2[1]));
        ul.appendChild(item);
        i++;
      }
      frag.appendChild(ul);
      continue;
    }
    if (line.trim() === '') { i++; continue; }
    const div = document.createElement('div');
    div.appendChild(inlineNodes(line));
    frag.appendChild(div);
    i++;
  }
  return frag;
}

function sendTask() {
  const input = document.getElementById('chat-input');
  const task = input.value.trim();
  if (!task) return;
  input.value = '';
  chatMessages.push({role: 'user', raw: task});
  appendMsg('user', task);
  chatMessages.push({role: 'agent', raw: ''});
  const bubble = appendMsg('agent', '');
  const idx = chatMessages.length - 1;
  const es = new EventSource('/events?task=' + encodeURIComponent(task) + '&workdir=' + encodeURIComponent(state.workspace));
  es.onmessage = function (e) {
    if (e.data === '[DONE]') {
      es.close();
      chatMessages[idx].raw += '\\n✓ 完成';
      bubble._raw = chatMessages[idx].raw;
      renderBubble(bubble);
      refreshFiles();
      return;
    }
    chatMessages[idx].raw += JSON.parse(e.data).text;
    bubble._raw = chatMessages[idx].raw;
    renderBubble(bubble);
    const h = document.getElementById('chat-history');
    h.scrollTop = h.scrollHeight;
  };
  es.onerror = function () { es.close(); };
}

/* ---------- 中央编辑器（Monaco，CDN；离线回退行号视图） ---------- */
function buildEditor() {
  document.getElementById('pane-center').innerHTML = `
    <div id="file-header">
      <span id="file-tab">—</span>
    </div>
    <div id="editor-host"><div class="placeholder">点击左侧文件树查看代码</div></div>`;
  ensureMonaco(function () {
    if (window.monaco) {
      editor = monaco.editor.create(document.getElementById('editor-host'), {
        value: '',
        language: 'plaintext',
        theme: 'vs',
        automaticLayout: true,
        fontSize: 13,
        minimap: { enabled: false },
      });
    } else {
      const host = document.getElementById('editor-host');
      host.className = 'file-view';
      host.innerHTML = '';
    }
  });
}

function ensureMonaco(cb) {
  if (window.monaco) { cb(); return; }
  if (window.require) {
    require(['vs/editor/editor.main'], function () { cb(); });
  } else {
    cb();
  }
}

function langOf(name) {
  const ext = (name.split('.').pop() || '').toLowerCase();
  const map = {py: 'python', js: 'javascript', ts: 'typescript', json: 'json', md: 'markdown',
    html: 'html', css: 'css', java: 'java', c: 'c', cpp: 'cpp', go: 'go', rs: 'rust',
    sh: 'shell', yml: 'yaml', yaml: 'yaml', toml: 'ini'};
  return map[ext] || 'plaintext';
}

async function refreshFiles() {
  try {
    const resp = await fetch('/tree?workdir=' + encodeURIComponent(state.workspace));
    const data = await resp.json();
    if (!data.ok) return;
    const files = data.tree.filter(e => e.type === 'file');
    if (document.getElementById('tree-root')) loadTree();
    files.sort((a, b) => (b.mtime || 0) - (a.mtime || 0));
    if (files.length) loadFile(files[0].name);
  } catch (e) { /* 忽略 */ }
}

async function loadFile(name) {
  try {
    const resp = await fetch('/file?workdir=' + encodeURIComponent(state.workspace) + '&path=' + encodeURIComponent(name));
    const data = await resp.json();
    const tab = document.getElementById('file-tab');
    if (data.ok) {
      if (tab) { tab.textContent = data.name; tab.style.display = ''; }
      if (editor) {
        editor.setValue(data.content);
        monaco.editor.setModelLanguage(editor.getModel(), langOf(data.name));
      } else {
        renderFile(data.content);
      }
    } else {
      if (tab) tab.style.display = 'none';
      const view = document.getElementById('editor-host');
      if (view) view.innerHTML = '<div class="placeholder">' + (data.error || '加载失败') + '</div>';
    }
  } catch (e) {
    const view = document.getElementById('editor-host');
    if (view) view.innerHTML = '<div class="placeholder">请求失败</div>';
  }
}

function renderFile(content) {
  const view = document.getElementById('editor-host');
  if (!view) return;
  view.innerHTML = '';
  content.split('\\n').forEach(function (line, i) {
    const div = document.createElement('div');
    const num = document.createElement('span');
    num.className = 'ln';
    num.textContent = String(i + 1);
    div.appendChild(num);
    div.appendChild(document.createTextNode(line === '' ? ' ' : line));
    view.appendChild(div);
  });
}

/* ---------- 文件树（Editor 左栏） ---------- */
function buildFileTree() {
  document.getElementById('pane-left').innerHTML = `
    <div class="tree-title">资源管理器</div>
    <div id="tree-root"></div>`;
  loadTree();
}

async function loadTree() {
  try {
    const resp = await fetch('/tree?workdir=' + encodeURIComponent(state.workspace) + '&deep=1');
    const data = await resp.json();
    const root = document.getElementById('tree-root');
    if (!root) return;
    root.innerHTML = '';
    if (!data.ok) {
      root.innerHTML = '<div class="mgr-status err">' + (data.error || '加载失败') + '</div>';
      return;
    }
    data.tree.forEach(n => root.appendChild(renderTreeNode(n)));
  } catch (e) { /* 忽略 */ }
}

function renderTreeNode(n) {
  const div = document.createElement('div');
  div.className = 'tree-node';
  const label = document.createElement('span');
  label.className = 'tree-label ' + (n.type === 'dir' ? 'dir' : 'file');
  label.textContent = (n.type === 'dir' ? '📁 ' : '📄 ') + n.name;
  div.appendChild(label);
  if (n.type === 'file') {
    label.onclick = () => loadFile(n.path);
  } else {
    label.onclick = () => {
      const kids = div.querySelector('.tree-kids');
      if (kids) kids.style.display = kids.style.display === 'none' ? '' : 'none';
    };
    const kids = document.createElement('div');
    kids.className = 'tree-kids';
    (n.children || []).forEach(c => kids.appendChild(renderTreeNode(c)));
    div.appendChild(kids);
  }
  return div;
}

/* ---------- 终端（Editor 底部） ---------- */
function buildTerminal() {
  document.getElementById('terminal-panel').innerHTML = `
    <div id="term-header">
      <span>终端</span>
      <span id="term-toggle" onclick="toggleTerminal()">折叠</span>
    </div>
    <div id="term-body">
      <div id="term-output"></div>
      <div id="term-inputbar">
        <span id="term-prompt">&gt;</span>
        <input id="term-input" placeholder="执行命令，如 python main.py">
      </div>
    </div>`;
  document.getElementById('term-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); runTerm(); }
  });
}

function toggleTerminal() {
  const body = document.getElementById('term-body');
  const toggle = document.getElementById('term-toggle');
  if (body.style.display === 'none') { body.style.display = ''; toggle.textContent = '折叠'; }
  else { body.style.display = 'none'; toggle.textContent = '展开'; }
}

async function runTerm() {
  const input = document.getElementById('term-input');
  const cmd = input.value.trim();
  if (!cmd) return;
  input.value = '';
  appendTerm('$ ' + cmd);
  try {
    const resp = await fetch('/exec', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({workdir: state.workspace, command: cmd}),
    });
    const data = await resp.json();
    if (data.ok) {
      if (data.dangerous) appendTerm('⚠️ 检测到危险命令', 'warn');
      appendTerm(data.output);
    } else {
      appendTerm('错误：' + data.error, 'err');
    }
  } catch (e) {
    appendTerm('请求失败：' + e, 'err');
  }
}

function appendTerm(text, cls) {
  const out = document.getElementById('term-output');
  const div = document.createElement('div');
  if (cls) div.className = 'term-' + cls;
  div.textContent = text;
  out.appendChild(div);
  out.scrollTop = out.scrollHeight;
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


def _workspace_tree(workdir: str, deep: bool = False, max_depth: int = 5) -> list[dict]:
    """工作区条目：默认顶层平铺（校验/下拉用）；deep=True 返回递归树（文件树用）。"""
    root = Path(workdir)
    if not root.is_dir():
        raise ValueError(f"工作区不存在：{workdir}")
    if not deep:
        entries = []
        for p in sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if p.name.startswith(".") or p.name in _SKIP_DIRS:
                continue
            entry = {"name": p.name, "type": "dir" if p.is_dir() else "file"}
            if p.is_file():
                entry["mtime"] = p.stat().st_mtime  # 供前端选「最新修改文件」
            entries.append(entry)
        return entries

    def walk(d: Path, depth: int) -> list[dict]:
        items = []
        for p in sorted(d.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if p.name.startswith(".") or p.name in _SKIP_DIRS:
                continue
            rel = str(p.relative_to(root))
            if p.is_dir():
                items.append({
                    "name": p.name,
                    "path": rel,
                    "type": "dir",
                    "children": walk(p, depth + 1) if depth < max_depth else [],
                })
            else:
                items.append({
                    "name": p.name,
                    "path": rel,
                    "type": "file",
                    "mtime": p.stat().st_mtime,
                })
        return items

    return walk(root, 1)


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
        elif self.path.startswith("/file"):
            self._handle_file()
        else:
            self.send_error(404)

    def _handle_tree(self) -> None:
        """工作区校验 + 文件树（deep=1 递归）。"""
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        workdir = (query.get("workdir") or [None])[0] or self.server.workdir
        deep = (query.get("deep") or ["0"])[0] in ("1", "true")
        try:
            tree = _workspace_tree(workdir, deep=deep)
            result = {"ok": True, "workdir": workdir, "tree": tree}
        except Exception as exc:  # noqa: BLE001
            result = {"ok": False, "error": str(exc)}
        data = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_file(self) -> None:
        """读取工作区内文件内容（路径越界防护）。"""
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        workdir = (query.get("workdir") or [None])[0] or self.server.workdir
        rel = (query.get("path") or [""])[0]
        try:
            root = Path(workdir).resolve()
            if not root.is_dir():
                raise ValueError(f"工作区不存在：{workdir}")
            target = (root / rel).resolve()
            if not str(target).startswith(str(root)):
                raise ValueError(f"路径越界：{rel}")
            if not target.is_file():
                raise ValueError(f"文件不存在：{rel}")
            text = target.read_text(encoding="utf-8", errors="replace")
            if len(text) > 200_000:
                text = text[:200_000] + "\n...（文件过大已截断）"
            result = {"ok": True, "path": rel, "name": target.name, "content": text}
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
        elif self.path == "/exec":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                workdir = str(body.get("workdir") or self.server.workdir)
                command = str(body.get("command", "")).strip()
                if not command:
                    raise ValueError("命令为空")
                if not Path(workdir).is_dir():
                    raise ValueError(f"工作区不存在：{workdir}")
                output = execute_command({"command": command}, workdir)
                # 终端是用户直接输入（用户即确认者），仅标记危险命令供前端提示
                result = {"ok": True, "output": output, "dangerous": is_dangerous(command)}
            except Exception as exc:  # noqa: BLE001
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
