"""极简 Web 界面：自写标准库 HTTP 服务（不引入 Web 框架，零新依赖）。

入口：python -m agent.web [--host 127.0.0.1] [--port 8080] [--workdir .]
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
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
from .plan import make_plan
from .sessions import SessionStore
from .skills import (
    delete_workspace_skill,
    load_skills,
    save_workspace_skill,
    skill_summary,
    update_workspace_skill,
)
from .tools import READ_ONLY_TOOL_NAMES, tool_schemas_for
from .tools.shell_tools import execute_command, is_dangerous

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>编程智能体 · Coding Agent</title>
<style>
  :root {
    /* 色调模仿 DSH design-platform：冷调 bluish 中性 + DeepSeek 蓝 */
    --bg: #f5f6f7; --surface: #ffffff; --border: #e6e8eb;
    --border-l1: rgba(0, 0, 0, 0.04);
    --text: #0f1115; --muted: #81858c; --caption: #adb0b5;
    --accent: #4176e6; --accent-hover: #2f5fd0; --accent-soft: rgba(65, 118, 230, 0.08);
    --code-bg: #f9fafb; --ok: #22c55e; --err: #ef4444; --warn: #f59e0b;
    --tblk-ok: #22c55e; --tblk-err: #ef4444; /* 轨迹状态色（DSH 同款） */
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; background: var(--bg); color: var(--text); height: 100vh; height: 100dvh; display: flex; flex-direction: column; overflow: hidden; }
  /* 工作区管理器（欢迎页整页 + 弹层复用同一卡片） */
  #welcome { flex: 1; min-height: 0; overflow: auto; display: flex; align-items: center; justify-content: center; padding: 24px; }
  .mgr-card { background: var(--surface); border: 1px solid var(--border-l1); border-radius: 16px; padding: 40px 44px; width: 520px; max-width: 92vw; max-height: 92vh; overflow-y: auto; box-shadow: 0 2px 12px rgba(38,37,30,.06); display: flex; flex-direction: column; gap: 12px; }
  .mgr-title { font-size: 28px; font-weight: 700; text-align: center; letter-spacing: -.5px; }
  .mgr-sub { color: var(--muted); text-align: center; margin-bottom: 8px; }
  .btn { border: 1px solid var(--border-l1); background: var(--surface); color: var(--text); border-radius: 8px; padding: 10px 14px; cursor: pointer; font-size: 15px; }
  .btn:hover { background: var(--code-bg); }
  .btn-accent { background: var(--accent); color: #fff; border: none; font-weight: 600; }
  .btn-accent:disabled { background: #e3cfc4; cursor: not-allowed; }
  .btn-accent:not(:disabled):hover { background: var(--accent-hover); }
  .mgr-divider { height: 1px; background: var(--border); margin: 4px 0; }
  .mgr-path { padding: 10px 12px; border: 1px solid var(--border-l1); border-radius: 8px; font-size: 14px; font-family: Consolas, monospace; width: 100%; }
  .mgr-status { font-size: 14px; min-height: 18px; color: var(--muted); }
  .mgr-status.ok { color: var(--ok); }
  .mgr-status.err { color: var(--err); }
  .mgr-recents-title { font-size: 14px; color: var(--muted); }
  .recent { padding: 8px 10px; border-radius: 8px; cursor: pointer; font-family: Consolas, monospace; font-size: 14px; display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  .recent:hover { background: var(--accent-soft); }
  .recent .path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
  .recent .del { color: var(--muted); font-weight: 700; padding: 0 4px; flex-shrink: 0; }
  .recent .del:hover { color: var(--err); }
  .mgr-cancel { border: none; background: none; color: var(--muted); cursor: pointer; font-size: 14px; padding: 6px; }
  /* 主布局骨架 */
  #main { display: none; flex: 1; min-height: 0; height: 100vh; height: 100dvh; flex-direction: column; overflow: hidden; }
  #topbar { display: flex; flex-shrink: 0; align-items: center; gap: 12px; padding: 8px 20px; background: var(--surface); border-bottom: 1px solid var(--border-l1); overflow: hidden; }
  .brand { font-weight: 700; font-size: 15px; letter-spacing: -.3px; white-space: nowrap; }
  .ws-chip { margin-left: auto; display: flex; align-items: center; gap: 8px; font-family: Consolas, monospace; font-size: 14px; border: 1px solid var(--border-l1); border-radius: 8px; padding: 6px 12px; background: var(--bg); max-width: 45vw; overflow: hidden; }
  #ws-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ws-chip button { border: none; background: none; cursor: pointer; color: var(--accent); font-size: 14px; font-weight: 600; }
  /* 会话栏（迭代 7 · 7.2） */
  .sess-bar { display: flex; align-items: center; gap: 6px; }
  .sess-bar select { border: 1px solid var(--border-l1); background: var(--bg); color: var(--text); border-radius: 8px; padding: 6px 10px; font-size: 14px; max-width: 240px; }
  .sess-bar button { border: none; background: var(--bg); color: var(--muted); border-radius: 8px; padding: 7px 12px; cursor: pointer; font-size: 14px; line-height: 1; white-space: nowrap; }
  .sess-bar button:hover { background: var(--accent-soft); color: var(--accent); }
  .skills-btn { border: none; background: var(--bg); color: var(--muted); border-radius: 8px; padding: 7px 12px; cursor: pointer; font-size: 14px; line-height: 1; white-space: nowrap; margin-right: 8px; }
  .skills-btn:hover { background: var(--accent-soft); color: var(--accent); }
  /* 技能面板（迭代 9 · 9.3） */
  .skill-card { width: 680px; }
  .skill-row { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border: 1px solid var(--border-l1); border-radius: 10px; background: var(--bg); }
  .skill-name { font-weight: 600; font-size: 14px; flex-shrink: 0; }
  .skill-desc { flex: 1; color: var(--muted); font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .skill-tag { font-size: 12px; color: var(--muted); border: 1px solid var(--border-l1); border-radius: 6px; padding: 1px 7px; flex-shrink: 0; }
  .skill-tag.ws { color: var(--accent); border-color: var(--accent); }
  .skill-actions { flex-shrink: 0; }
  .skill-actions button { border: none; background: none; cursor: pointer; font-size: 14px; color: var(--muted); padding: 2px 5px; }
  .skill-actions button:hover { color: var(--accent); }
  .skill-actions button.del:hover { color: var(--err); }
  .skill-form input, .skill-form textarea { width: 100%; border: 1px solid var(--border-l1); border-radius: 8px; padding: 8px 10px; font-size: 13px; margin-bottom: 8px; font-family: inherit; background: var(--bg); color: var(--text); box-sizing: border-box; }
  .skill-form textarea { min-height: 130px; resize: vertical; font-family: Consolas, monospace; }
  .skill-form .skill-err { color: var(--err); font-size: 13px; min-height: 18px; }
  #content { flex: 1; min-height: 0; height: 0; display: flex; overflow: hidden; }
  .pane { display: flex; flex-direction: column; overflow: hidden; min-height: 0; min-width: 0; }
  #pane-left { width: 240px; }
  #pane-center { flex: 1; min-width: 0; }
  #pane-right { width: 380px; }
  .splitter { width: 4px; cursor: col-resize; flex-shrink: 0; background: linear-gradient(90deg, transparent calc(50% - 0.5px), var(--border) calc(50% - 0.5px), var(--border) calc(50% + 0.5px), transparent calc(50% + 0.5px)); }
  .splitter:hover { background: rgba(65, 118, 230, 0.25); }
  #editor-host { flex: 1; min-height: 0; }
  .placeholder { color: var(--muted); font-size: 15px; display: flex; align-items: center; justify-content: center; height: 100%; border: 1px dashed var(--border); border-radius: 12px; margin: 16px; }
  /* 对话区（右侧聊天面板） */
  #chat-history { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 16px; display: flex; flex-direction: column; gap: 14px; }
  .chat-hint { color: var(--muted); font-size: 14px; padding: 2px 0; }
  .msg-col { display: flex; flex-direction: column; max-width: 85%; }
  .msg.user .msg-col { align-items: flex-end; }
  .msg.agent .msg-col { align-items: flex-start; }
  .role-label { font-size: 12px; color: var(--caption); margin-bottom: 4px; }
  #chat-inputbar { display: flex; flex-shrink: 0; gap: 10px; padding: 12px 16px 16px; background: var(--surface); border-top: 1px solid var(--border-l1); align-items: flex-end; position: relative; }
  .input-wrap { flex: 1; position: relative; display: flex; min-width: 0; }
  /* 输入框左侧模式切换按钮（迭代 8 · 8.6） */
  .mode-btn { flex-shrink: 0; border: 1px solid var(--border-l1); background: var(--bg); color: var(--muted); border-radius: 999px; padding: 10px 14px; cursor: pointer; font-size: 13px; white-space: nowrap; line-height: 1; }
  .mode-btn.agent { background: var(--accent-soft); color: var(--accent); border-color: transparent; font-weight: 600; }
  .mode-btn.chat { background: var(--accent-soft); color: var(--accent); border-color: transparent; font-weight: 600; }
  /* / 命令浮层 */
  .cmd-pop { position: absolute; left: 0; right: 0; bottom: calc(100% + 8px); display: none; flex-direction: column; gap: 2px; padding: 6px; background: var(--surface); border: 1px solid var(--border-l1); border-radius: 12px; box-shadow: 0 8px 24px rgba(15, 17, 21, 0.10); z-index: 20; max-height: 240px; overflow: auto; }
  .cmd-pop.open { display: flex; }
  .cmd-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 8px; cursor: pointer; }
  .cmd-item:hover, .cmd-item.sel { background: var(--accent-soft); }
  .cmd-icon { font-size: 14px; flex-shrink: 0; }
  .cmd-name { font-weight: 600; font-size: 13px; flex-shrink: 0; }
  .cmd-desc { margin-left: auto; color: var(--muted); font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  #chat-input { flex: 1; resize: none; height: 44px; padding: 10px 14px; border: 1px solid var(--border-l1); border-radius: 16px; font-size: 14px; font-family: inherit; background: var(--surface); color: var(--text); outline: none; }
  #chat-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(65, 118, 230, 0.12); }
  .send-btn { padding: 10px 22px; background: var(--accent); color: #fff; border: none; border-radius: 999px; cursor: pointer; font-weight: 600; font-size: 14px; white-space: nowrap; }
  .send-btn:hover { background: var(--accent-hover); }
  .msg { display: flex; }
  .msg.user { justify-content: flex-end; }
  .bubble { max-width: 85%; padding: 8px 12px; border-radius: 12px; white-space: pre-wrap; word-break: break-word; font-size: 14px; line-height: 1.55; }
  .msg.user .bubble { background: var(--accent); color: #fff; border-radius: 22px; padding: 10px 16px; }
  .msg.agent .bubble { background: transparent; border: none; padding: 2px 0; line-height: 1.65; }
  .tool { color: var(--accent-hover); font-weight: 600; }
  .obs { color: var(--ok); }
  .bubble pre { background: var(--code-bg); border: 1px solid var(--border-l1); border-radius: 6px; padding: 8px; margin: 4px 0; overflow-x: auto; }
  .bubble code.ic { background: var(--code-bg); border: 1px solid var(--border-l1); border-radius: 4px; padding: 0 4px; font-size: 13px; }
  .bubble h1, .bubble h2, .bubble h3, .bubble h4 { margin: 6px 0 2px; font-size: 1.02em; }
  .bubble ul { margin: 2px 0; padding-left: 18px; }
  .bubble a { color: var(--accent); }
  /* 轨迹折叠块（迭代 7 · 7.4-UI：模仿 DSH DisclosureRow） */
  .trace { display: flex; flex-direction: column; gap: 2px; margin-bottom: 8px; width: 100%; }
  .tblk { font-size: 13px; }
  .tblk-head { display: flex; align-items: center; gap: 6px; padding: 3px 6px; cursor: pointer; user-select: none; border-radius: 6px; }
  .tblk-head:hover { background: rgba(0, 0, 0, 0.03); }
  .tblk-icon { flex-shrink: 0; font-size: 13px; }
  .tblk-title { font-weight: 400; flex-shrink: 0; }
  .tblk-sep { flex: none; width: 2px; height: 2px; margin: 0 2px; border-radius: 1px; background: var(--muted); }
  .tblk-summary { min-width: 0; flex: 1 1 auto; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--muted); font-size: 13px; }
  .tblk-meta { flex-shrink: 0; color: var(--muted); font-size: 12px; }
  .tblk-arrow { flex-shrink: 0; color: var(--muted); }
  /* 运行态扫光（DSH reasoning/command sweep） */
  .tblk.running .tblk-head { position: relative; overflow: hidden; }
  .tblk.running .tblk-head::after { content: ''; position: absolute; top: 0; bottom: 0; left: -300px; width: 300px; background: linear-gradient(90deg, transparent 0%, rgba(247, 247, 244, 0.9) 55%, transparent 100%); animation: tblk-sweep 2.6s ease-out infinite; pointer-events: none; }
  @keyframes tblk-sweep { 0% { left: -300px; } 90%, 100% { left: 100%; } }
  @media (prefers-reduced-motion: reduce) { .tblk.running .tblk-head::after { display: none; animation: none; } }
  /* 展开正文：tool/note/err = 代码卡片；think = 标题下缩进文本 */
  .tblk.tool .tblk-body, .tblk.note .tblk-body, .tblk.err .tblk-body, .tblk.todo .tblk-body, .tblk.sub .tblk-body { display: none; margin: 4px 0 4px 4px; padding: 12px 16px; max-height: 260px; overflow: auto; border: 1px solid rgba(0, 0, 0, 0.04); border-radius: 12px; background: #f9fafb; color: var(--text); font-family: Consolas, monospace; font-size: 12.5px; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
  .tblk.think .tblk-body { display: none; padding: 4px 0 4px 22px; max-height: 260px; overflow: auto; color: var(--muted); font-size: 13px; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
  .tblk.tool.ok .tblk-meta { color: var(--tblk-ok); }
  .tblk.tool.err .tblk-meta, .tblk.err .tblk-title, .tblk.err .tblk-icon { color: var(--tblk-err); }
  .tblk.sub.ok .tblk-meta { color: var(--tblk-ok); }
  .tblk.sub.err .tblk-meta { color: var(--tblk-err); }
  .tblk.note .tblk-body { color: var(--muted); }
  /* 回合统计行（模仿 DSH StatsLine） */
  .turn-stats { margin: 2px 0 6px; color: var(--muted); font-size: 12.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  /* 重试行（迭代 7 · 7.5） */
  .tblk.retry .tblk-icon, .tblk.retry .tblk-title { color: var(--warn); }
  .tblk.retry .tblk-head { cursor: default; }
  .tblk.warn .tblk-icon, .tblk.warn .tblk-title { color: var(--warn); }
  .tblk.warn .tblk-head { cursor: default; }
  .tblk.tool.warn .tblk-meta { color: var(--warn); }
  /* 回合状态指示（迭代 7 · 7.5） */
  .turn-status { margin-left: 6px; font-size: 12px; color: var(--caption); }
  .turn-status::before { content: ''; display: inline-block; width: 6px; height: 6px; border-radius: 3px; background: var(--accent); margin-right: 4px; vertical-align: middle; animation: status-pulse 1.2s ease-in-out infinite; }
  @keyframes status-pulse { 50% { opacity: 0.35; } }
  .turn-status.done { color: var(--muted); }
  .turn-status.done::before { background: var(--ok); animation: none; }
  .turn-status.err { color: var(--err); }
  .turn-status.err::before { background: var(--err); animation: none; }
  @media (prefers-reduced-motion: reduce) { .turn-status::before { animation: none; } }
  /* 文件页（右栏） */
  #file-header { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 12px 16px 8px; }
  #file-tab { display: none; font-family: Consolas, monospace; font-size: 14px; font-weight: 600; background: var(--surface); border: 1px solid var(--border-l1); border-radius: 6px 6px 0 0; padding: 6px 12px; }
  #file-save { display: none; border: 1px solid var(--border-l1); background: var(--surface); color: var(--text); border-radius: 8px; padding: 6px 14px; cursor: pointer; font-size: 14px; font-weight: 600; }
  #file-save:hover { border-color: var(--accent); color: var(--accent); }
  #file-view, .file-view { flex: 1; margin: 0 16px 16px; background: var(--code-bg); border: 1px solid var(--border-l1); border-radius: 8px; padding: 12px; overflow: hidden; font-family: Consolas, monospace; font-size: 14px; line-height: 1.5; display: flex; flex-direction: row; }
  .fv-nums { width: 48px; flex-shrink: 0; overflow: hidden; color: var(--muted); text-align: right; padding-right: 12px; white-space: pre; user-select: none; }
  .fv-ta { flex: 1; border: none; outline: none; background: transparent; resize: none; font-family: Consolas, monospace; font-size: 14px; line-height: 1.5; color: var(--text); padding: 0 0 0 12px; overflow: auto; overscroll-behavior: contain; }
  /* 文件树（Editor 左栏） */
  .tree-title { font-size: 13px; font-weight: 700; color: var(--muted); padding: 10px 16px 6px; letter-spacing: .3px; }
  #tree-root { flex: 1; min-height: 0; overflow: auto; overscroll-behavior: contain; padding: 4px 8px 16px; }
  .tree-node { font-size: 14px; }
  .tree-label { display: block; padding: 3px 6px; border-radius: 6px; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .tree-label:hover { background: var(--accent-soft); }
  .tree-label.file { font-family: Consolas, monospace; }
  .tree-kids { padding-left: 14px; }
  /* 弹层 */
  #modal { display: none; position: fixed; inset: 0; background: rgba(38,37,30,.45); align-items: center; justify-content: center; z-index: 10; padding: 24px; }
  #modal .mgr-card { box-shadow: 0 8px 40px rgba(38,37,30,.2); }
</style>
<script async src="https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs/loader.js" onload="monacoCdn('jsdelivr')" onerror="fallbackMonaco()"></script>
<script>
  function monacoCdn(which) {
    const base = which === 'jsdelivr'
      ? 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs'
      : 'https://unpkg.com/monaco-editor@0.52.0/min/vs';
    try {
      require.config({ paths: { vs: base } });
      require(['vs/editor/editor.main'], function () { window.monacoReady = true; });
    } catch (e) { window.require = undefined; }
  }
  function fallbackMonaco() {
    const s = document.createElement('script');
    s.async = true;
    s.src = 'https://unpkg.com/monaco-editor@0.52.0/min/vs/loader.js';
    s.onload = function () { monacoCdn('unpkg'); };
    s.onerror = function () { window.require = undefined; };
    document.head.appendChild(s);
  }
</script>
</head>
<body>
<div id="welcome"></div>
<div id="main">
  <div id="topbar">
    <span class="brand">🤖 编程智能体</span>
    <div class="sess-bar">
      <select id="sess-select" onchange="switchSession(this.value)" title="选择会话"></select>
      <button id="sess-new" onclick="createSession()" title="新建会话">新建会话</button>
      <button id="sess-rename" onclick="renameSession()" title="重命名当前会话">重命名</button>
      <button id="sess-del" onclick="deleteSession()" title="删除当前会话">删除</button>
    </div>
    <button class="skills-btn" onclick="openSkillsPanel()" title="浏览与管理技能（仅工作区技能可增删改）">📚 技能</button>
    <div class="ws-chip">
      <span id="ws-name"></span>
      <button onclick="openManager()" title="切换工作区">🔄 切换</button>
    </div>
  </div>
  <div id="content">
    <div id="pane-left" class="pane"></div>
    <div class="splitter" id="split1"></div>
    <div id="pane-center" class="pane"></div>
    <div class="splitter" id="split2"></div>
    <div id="pane-right" class="pane"></div>
  </div>
</div>
<div id="modal"><div id="modal-card"></div></div>
<script>
const state = {
  workspace: localStorage.getItem('agent.workspace') || '',
  mode: localStorage.getItem('agent.mode') || 'agent',
  recents: (function () {
    try { return JSON.parse(localStorage.getItem('agent.recents') || '[]'); }
    catch (e) { return []; }
  })(),
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
  // 切换工作区：会话归属工作区——重置当前会话与对话
  currentSessionId = null;
  firstTask = null;
  chatMessages = [];
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
  loadSessions(state.workspace);
  setMode(state.mode);
  closeManager();
}

function setMode(m) {
  state.mode = m === 'chat' ? 'chat' : 'agent';
  localStorage.setItem('agent.mode', state.mode);
  const btn = document.getElementById('mode-toggle');
  if (btn) {
    btn.textContent = state.mode === 'agent' ? '🤖 Agent' : '💬 Chat';
    btn.className = 'mode-btn ' + state.mode;
    btn.title = state.mode === 'agent'
      ? '当前 Agent 模式（可编辑文件）；点击切换到 chat 模式（只读）'
      : '当前 chat 模式（只读，不可编辑文件）；点击切换到 Agent 模式';
  }
}

function toggleMode() {
  setMode(state.mode === 'chat' ? 'agent' : 'chat');
}

function openManager() {
  document.getElementById('modal').style.display = 'flex';
  buildManager(document.getElementById('modal-card'));
}

function closeManager() {
  document.getElementById('modal').style.display = 'none';
  activeManager = document.getElementById('welcome');
}

/* ---------- 技能管理（迭代 9 · 9.3：浏览/新建/编辑/删除 + 只读标注） ---------- */
let skillDelTimer = null;

function skillSrcLabel(src) {
  if (src === 'workspace') return '工作区';
  if (src === 'env') return 'SKILLS_DIR';
  return '内置';
}

async function openSkillsPanel() {
  document.getElementById('modal').style.display = 'flex';
  const card = document.getElementById('modal-card');
  card.innerHTML = `
    <div class="mgr-card skill-card">
      <div class="mgr-title">📚 技能</div>
      <div class="mgr-sub">技能仅在你显式指定时装载（/skill <name>）；内置与 SKILLS_DIR 只读，工作区技能可增删改</div>
      <div id="skill-list"></div>
      <div class="mgr-divider"></div>
      <div style="display:flex; gap:8px;">
        <button class="btn-accent" onclick="showSkillForm()">＋ 新建技能</button>
        <button class="mgr-cancel" onclick="closeManager()">关闭</button>
      </div>
    </div>`;
  await refreshSkillList();
}

async function refreshSkillList() {
  const box = document.getElementById('skill-list');
  if (!box) return;
  box.innerHTML = '<div class="mgr-status">加载中…</div>';
  try {
    const resp = await fetch('/skills?workdir=' + encodeURIComponent(state.workspace || ''));
    const data = await resp.json();
    if (!data.ok) { box.innerHTML = '<div class="mgr-status err">✗ ' + (data.error || '加载失败') + '</div>'; return; }
    const skills = data.skills || [];
    if (!skills.length) { box.innerHTML = '<div class="mgr-status">暂无技能</div>'; return; }
    box.innerHTML = '';
    skills.forEach(renderSkillRow);
  } catch (e) {
    box.innerHTML = '<div class="mgr-status err">✗ 请求失败：' + e + '</div>';
  }
}

function renderSkillRow(s) {
  const box = document.getElementById('skill-list');
  if (!box) return;
  const row = document.createElement('div');
  row.className = 'skill-row';
  const nm = document.createElement('span');
  nm.className = 'skill-name';
  nm.textContent = '📘 ' + s.name;
  nm.title = '/skill ' + s.name + '（点击填入输入框）';
  nm.style.cursor = 'pointer';
  nm.onclick = function () {
    closeManager();
    const input = document.getElementById('chat-input');
    input.value = '/skill ' + s.name + ' ';
    input.focus();
  };
  const ds = document.createElement('span');
  ds.className = 'skill-desc';
  ds.textContent = s.description || '（无描述）';
  ds.title = 'modes: ' + ((s.modes || []).join(', ') || 'agent');
  const tag = document.createElement('span');
  tag.className = 'skill-tag' + (s.source === 'workspace' ? ' ws' : '');
  tag.textContent = skillSrcLabel(s.source) + (s.source !== 'workspace' ? ' · 只读' : '');
  row.appendChild(nm);
  row.appendChild(ds);
  row.appendChild(tag);
  if (s.source === 'workspace') {
    const acts = document.createElement('span');
    acts.className = 'skill-actions';
    const ed = document.createElement('button');
    ed.textContent = '✎';
    ed.title = '编辑技能 ' + s.name;
    ed.onclick = function () { showSkillForm(s); };
    const del = document.createElement('button');
    del.className = 'del';
    del.textContent = '🗑';
    del.title = '删除技能 ' + s.name;
    del.onclick = function () { askDeleteSkill(s.name, del); };
    acts.appendChild(ed);
    acts.appendChild(del);
    row.appendChild(acts);
  }
  box.appendChild(row);
}

function showSkillForm(existing) {
  const card = document.getElementById('modal-card');
  const isEdit = !!existing;
  card.innerHTML = `
    <div class="mgr-card skill-card skill-form">
      <div class="mgr-title">${isEdit ? '✎ 编辑技能' : '＋ 新建技能'}</div>
      <div class="mgr-sub">技能 = 目录 + SKILL.md；保存即写入工作区 .codeagent/skills/，下次运行立即生效</div>
      <input id="sk-name" placeholder="技能名（字母/数字/-/_，1–40 字符，如 python-testing）">
      <input id="sk-desc" placeholder="一句话描述，如：Python 单元测试规范">
      <input id="sk-kw" placeholder="关键词，逗号分隔，如：pytest, 单测, 测试">
      <input id="sk-modes" placeholder="适用模式，逗号分隔（默认 agent）">
      <textarea id="sk-body" placeholder="指南正文（≤4000 字）"></textarea>
      <div class="skill-err" id="sk-err"></div>
      <div style="display:flex; gap:8px;">
        <button class="btn-accent" onclick="saveSkill(${isEdit ? 'true' : 'null'})">保存</button>
        <button class="btn" onclick="openSkillsPanel()">取消</button>
      </div>
    </div>`;
  const nameEl = document.getElementById('sk-name');
  if (isEdit) { nameEl.value = existing.name; nameEl.disabled = true; }
  document.getElementById('sk-desc').value = isEdit ? (existing.description || '') : '';
  document.getElementById('sk-kw').value = isEdit ? (existing.keywords || []).join(', ') : '';
  document.getElementById('sk-modes').value = isEdit ? (existing.modes || []).join(', ') : '';
  document.getElementById('sk-body').value = isEdit ? (existing.body || '') : '';
}

async function saveSkill(isEdit) {
  const nameEl = document.getElementById('sk-name');
  const errEl = document.getElementById('sk-err');
  const name = (nameEl ? nameEl.value : '').trim();
  const payload = {
    workdir: state.workspace || '',
    description: document.getElementById('sk-desc').value,
    keywords: document.getElementById('sk-kw').value,
    modes: document.getElementById('sk-modes').value,
    body: document.getElementById('sk-body').value,
  };
  if (!isEdit) payload.name = name;
  try {
    const resp = await fetch(isEdit ? ('/skills/' + encodeURIComponent(name)) : '/skills', {
      method: isEdit ? 'PUT' : 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (data.ok) { openSkillsPanel(); return; }
    if (errEl) errEl.textContent = '✗ ' + (data.error || '保存失败');
  } catch (e) {
    if (errEl) errEl.textContent = '✗ 请求失败：' + e;
  }
}

function askDeleteSkill(name, btn) {
  if (btn.dataset.armed === '1') {
    btn.dataset.armed = '';
    btn.textContent = '🗑';
    clearTimeout(skillDelTimer);
    doDeleteSkill(name);
    return;
  }
  btn.dataset.armed = '1';
  btn.textContent = '确认删除？';
  clearTimeout(skillDelTimer);
  skillDelTimer = setTimeout(function () {
    btn.dataset.armed = '';
    btn.textContent = '🗑';
  }, 3000);
}

async function doDeleteSkill(name) {
  try {
    const resp = await fetch('/skills/' + encodeURIComponent(name) + '?workdir=' + encodeURIComponent(state.workspace || ''), {method: 'DELETE'});
    const data = await resp.json();
    if (!data.ok) {
      const box = document.getElementById('skill-list');
      if (box) box.insertAdjacentHTML('afterbegin', '<div class="mgr-status err">✗ ' + (data.error || '删除失败') + '</div>');
    }
  } catch (e) { /* 列表刷新兜底 */ }
  openSkillsPanel();
}

let chatMessages = [];
let editor = null;
let currentFile = null;

/* ---------- 会话管理（迭代 7 · 切片 7.2：列表/新建/切换/重命名/删除 + 消息落盘） ---------- */
let currentSessionId = null;
let sessionSaving = false;
let savePending = false;
let firstTask = null;

async function loadSessions(ws) {
  try {
    const wsArg = ws !== undefined ? ws : state.workspace;
    const resp = await fetch('/sessions?workspace=' + encodeURIComponent(wsArg || ''));
    const data = await resp.json();
    if (!data.ok) return;
    const sel = document.getElementById('sess-select');
    if (!sel) return;
    sel.innerHTML = '<option value="">（新会话）</option>';
    data.sessions.forEach(function (s) {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.name || s.id;
      sel.appendChild(opt);
    });
    // 当前会话不属于该工作区时自动置空（会话归属工作区）
    if (currentSessionId && !data.sessions.some(function (s) { return s.id === currentSessionId; })) {
      currentSessionId = null;
    }
    sel.value = currentSessionId || '';
  } catch (e) { /* 忽略 */ }
}

async function ensureSession(task) {
  if (currentSessionId) return;
  try {
    const resp = await fetch('/sessions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({workspace: state.workspace, name: (task || '新会话').slice(0, 24)}),
    });
    const data = await resp.json();
    if (data.ok && data.session) {
      currentSessionId = data.session.id;
      await loadSessions(state.workspace);
    }
  } catch (e) { /* 忽略 */ }
}

async function switchSession(id) {
  if (!id) return;
  try {
    const resp = await fetch('/sessions/' + encodeURIComponent(id));
    const data = await resp.json();
    if (!data.ok || !data.session) return;
    const s = data.session;
    currentSessionId = s.id;
    firstTask = null;
    state.workspace = s.workspace || state.workspace;
    localStorage.setItem('agent.workspace', state.workspace);
    document.getElementById('ws-name').textContent = state.workspace;
    chatMessages = (s.messages || []).map(function (m) { return {role: m.role, raw: m.raw, trace: m.trace}; });
    markInterruptedTurn();  // 上次中断的末轮打标记
    buildChat('pane-right');
    loadSessions(s.workspace);  // 会话归属工作区：下拉仅显示本工作区会话
    loadTree();
    refreshFiles();
  } catch (e) { /* 忽略 */ }
}

async function createSession() {
  try {
    const resp = await fetch('/sessions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({workspace: state.workspace, name: '新会话'}),
    });
    const data = await resp.json();
    if (!data.ok || !data.session) return;
    currentSessionId = data.session.id;
    firstTask = null;
    await loadSessions();
    chatMessages = [];
    buildChat('pane-right');
  } catch (e) { /* 忽略 */ }
}

async function renameSession() {
  if (!currentSessionId) return;
  const sel = document.getElementById('sess-select');
  const old = sel && sel.selectedIndex >= 0 ? sel.options[sel.selectedIndex].textContent : '';
  const name = window.prompt('会话名称：', old);
  if (name === null || !name.trim()) return;
  try {
    const resp = await fetch('/sessions/' + encodeURIComponent(currentSessionId), {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name}),
    });
    const data = await resp.json();
    if (data.ok) await loadSessions();
  } catch (e) { /* 忽略 */ }
}

async function deleteSession() {
  if (!currentSessionId) return;
  if (!window.confirm('删除当前会话及其对话记录？')) return;
  const id = currentSessionId;
  currentSessionId = null;
  firstTask = null;
  chatMessages = [];
  buildChat('pane-right');
  try {
    await fetch('/sessions/' + encodeURIComponent(id), {method: 'DELETE'});
    await loadSessions();
  } catch (e) { /* 忽略 */ }
}

async function saveMessages() {
  if (!currentSessionId) return;
  if (sessionSaving) { savePending = true; return; }
  sessionSaving = true;
  do {
    savePending = false;
    try {
      await fetch('/sessions/' + encodeURIComponent(currentSessionId) + '/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({messages: chatMessages}),
      });
    } catch (e) { /* 忽略 */ }
  } while (savePending);
  sessionSaving = false;
}

/* 首次会话自动命名：按首条用户任务压缩空白、截断 20 字 */
function sessionTitle(task) {
  const t = String(task || '').replace(/\\s+/g, ' ').trim();
  if (!t) return '新会话';
  return t.length > 20 ? t.slice(0, 20) + '…' : t;
}

async function autoRenameSession(task) {
  if (!currentSessionId) return;
  const name = sessionTitle(task);
  try {
    await fetch('/sessions/' + encodeURIComponent(currentSessionId), {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name}),
    });
    await loadSessions();
  } catch (e) { /* 忽略 */ }
}

function initSplitters() {
  const left = document.getElementById('pane-left');
  const right = document.getElementById('pane-right');
  const center = document.getElementById('pane-center');
  let leftW = Math.min(800, Math.max(120, parseInt(localStorage.getItem('agent.paneLeft') || '240', 10)));
  let rightW = Math.min(800, Math.max(120, parseInt(localStorage.getItem('agent.paneRight') || '380', 10)));
  const apply = () => {
    left.style.width = leftW + 'px';
    left.style.flex = 'none';
    right.style.width = rightW + 'px';
    right.style.flex = 'none';
    center.style.flex = '1';
  };
  apply();
  // 缩放/窄窗口自适应：左右栏宽按视口钳制，右栏（对话框）永不越界
  const clamp = () => {
    const maxSide = Math.max(140, Math.floor(window.innerWidth * 0.38));
    if (leftW > maxSide) { leftW = maxSide; localStorage.setItem('agent.paneLeft', String(leftW)); }
    if (rightW > maxSide) { rightW = maxSide; localStorage.setItem('agent.paneRight', String(rightW)); }
    apply();
  };
  clamp();
  window.addEventListener('resize', function () { clamp(); });
  const drag = (splitter, isLeft) => {
    splitter.addEventListener('mousedown', function (e) {
      e.preventDefault();
      const startX = e.clientX;
      const startW = isLeft ? leftW : rightW;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      const move = ev => {
        const w = isLeft ? startW + (ev.clientX - startX) : startW - (ev.clientX - startX);
        if (w < 120 || w > 800) return;
        if (isLeft) { leftW = w; localStorage.setItem('agent.paneLeft', String(w)); }
        else { rightW = w; localStorage.setItem('agent.paneRight', String(w)); }
        apply();
      };
      const up = () => {
        document.removeEventListener('mousemove', move);
        document.removeEventListener('mouseup', up);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
      document.addEventListener('mousemove', move);
      document.addEventListener('mouseup', up);
    });
  };
  drag(document.getElementById('split1'), true);
  drag(document.getElementById('split2'), false);
}

function buildLayout() {
  try { buildFileTree(); } catch (e) { console.error('buildFileTree', e); }
  try { buildEditor(); } catch (e) { console.error('buildEditor', e); }
  try { buildChat('pane-right'); } catch (e) { console.error('buildChat', e); }
}

/* ---------- 对话（右侧聊天面板；状态存 chatMessages 重放） ---------- */
function buildChat(containerId) {
  document.getElementById(containerId).innerHTML = `
    <div id="chat-history">
      <div class="chat-hint">向 agent 发送编程任务，如「创建 hello.py 打印 Hello 并运行」</div>
    </div>
    <div id="chat-inputbar">
      <button id="mode-toggle" class="mode-btn" onclick="toggleMode()" title="切换模式"></button>
      <div class="input-wrap">
        <div id="cmd-pop" class="cmd-pop"></div>
        <textarea id="chat-input" placeholder="输入编程任务，Enter 发送（Shift+Enter 换行）；输入 / 选择命令"></textarea>
      </div>
      <button class="send-btn" onclick="sendTask()">发送</button>
    </div>`;
  chatMessages.forEach(m => appendMsg(m.role, m.raw, m.trace));
  const h = document.getElementById('chat-history');
  h.scrollTop = h.scrollHeight;
  setMode(state.mode);
  buildCmdPop();
}

function appendMsg(role, raw, trace) {
  const history = document.getElementById('chat-history');
  const hint = history.querySelector('.chat-hint');
  if (hint) hint.remove();
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + role;
  const col = document.createElement('div');
  col.className = 'msg-col';
  const label = document.createElement('div');
  label.className = 'role-label';
  label.textContent = role === 'user' ? '你' : 'Agent';
  col.appendChild(label);
  if (role === 'agent' && trace && trace.length) {
    const traceEl = document.createElement('div');
    traceEl.className = 'trace';
    col.appendChild(traceEl);
    renderTraceFromEvents(traceEl, trace);
  }
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble._raw = raw;
  col.appendChild(bubble);
  wrap.appendChild(col);
  history.appendChild(wrap);
  renderBubble(bubble);
  history.scrollTop = history.scrollHeight;
  return bubble;
}

function appendAgentMsg() {
  const history = document.getElementById('chat-history');
  const hint = history.querySelector('.chat-hint');
  if (hint) hint.remove();
  const wrap = document.createElement('div');
  wrap.className = 'msg agent';
  const col = document.createElement('div');
  col.className = 'msg-col';
  const label = document.createElement('div');
  label.className = 'role-label';
  label.textContent = 'Agent';
  const status = document.createElement('span');
  status.className = 'turn-status';
  label.appendChild(status);
  col.appendChild(label);
  const traceEl = document.createElement('div');
  traceEl.className = 'trace';
  col.appendChild(traceEl);
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  col.appendChild(bubble);
  wrap.appendChild(col);
  history.appendChild(wrap);
  history.scrollTop = history.scrollHeight;
  return {bubble: bubble, traceEl: traceEl, status: status};
}

/* ---------- 轨迹折叠块（迭代 7 · 7.4-UI，模仿 DSH DisclosureRow） ---------- */
function oneLine(s, n) {
  const t = String(s || '').replace(/\\s+/g, ' ').trim();
  return t.length > n ? t.slice(0, n) + '…' : t;
}

function latestLine(s) {
  const v = String(s || '').trimEnd();
  const i = v.lastIndexOf('\\n');
  return i === -1 ? v : v.slice(i + 1);
}

function formatMs(ms) {
  if (ms < 1000) return ms + 'ms';
  const s = Math.round(ms / 100) / 10;
  if (s < 60) return s + 's';
  return Math.floor(s / 60) + 'm' + Math.round(s % 60) + 's';
}

function createTblk(traceEl, kind) {
  const root = document.createElement('div');
  root.className = 'tblk ' + kind;
  const head = document.createElement('div');
  head.className = 'tblk-head';
  const icon = document.createElement('span');
  icon.className = 'tblk-icon';
  const title = document.createElement('span');
  title.className = 'tblk-title';
  const sep = document.createElement('span');
  sep.className = 'tblk-sep';
  const summary = document.createElement('span');
  summary.className = 'tblk-summary';
  const meta = document.createElement('span');
  meta.className = 'tblk-meta';
  const arrow = document.createElement('span');
  arrow.className = 'tblk-arrow';
  arrow.textContent = '▸';
  const body = document.createElement('div');
  body.className = 'tblk-body';
  body.style.display = 'none';
  head.appendChild(icon);
  head.appendChild(title);
  head.appendChild(sep);
  head.appendChild(summary);
  head.appendChild(meta);
  head.appendChild(arrow);
  head.onclick = function () {
    const open = body.style.display === 'none';
    body.style.display = open ? 'block' : 'none';
    arrow.textContent = open ? '▾' : '▸';
  };
  root.appendChild(head);
  root.appendChild(body);
  traceEl.appendChild(root);
  return {root: root, head: head, title: title, meta: meta, arrow: arrow, body: body, summary: summary};
}

function setBubbleRaw(bubble, raw) {
  if (!bubble) return;
  bubble._raw = raw;
  renderBubble(bubble);
}

function newTurnState(bubble, traceEl) {
  return {
    bubble: bubble, traceEl: traceEl,
    answerRaw: '', roundRaw: '', thinkRaw: '',
    think: null, pendingTools: [], traceEvents: [],
    steps: 0, toolMs: 0, statsEl: null,
    statusEl: null, connErr: false, done: false,
    todoBlk: null, pendingSubs: [],
  };
}

function setStatus(t, text, cls) {
  if (!t.statusEl) return;
  t.statusEl.textContent = text;
  t.statusEl.className = 'turn-status' + (cls ? ' ' + cls : '');
}

function handleEvent(ev, t) {
  t.traceEvents.push(ev);
  switch (ev.type) {
    case 'think_start':
      t.think = createTblk(t.traceEl, 'think');
      t.think.root.className = 'tblk think running';
      t.think.icon = t.think.head.children[0];
      t.think.icon.textContent = '🧠';
      t.think.title.textContent = 'Think';
      setStatus(t, '思考中…');
      break;
    case 'think_delta':
      t.thinkRaw += ev.text;
      if (t.think) {
        t.think.body.textContent = t.thinkRaw;
        t.think.summary.textContent = latestLine(t.thinkRaw);  // 流式跟随最新行
        try { t.think.summary.scrollLeft = t.think.summary.scrollWidth - t.think.summary.clientWidth; } catch (e) { /* 忽略 */ }
      }
      break;
    case 'think_end':
      if (t.think) {
        t.think.root.className = 'tblk think';
        t.think.summary.textContent = oneLine(t.thinkRaw, 60);  // 完成态显示首行
        t.think.meta.textContent = '(' + t.thinkRaw.length + ' 字)';
        t.think = null;
        t.thinkRaw = '';
      }
      break;
    case 'content_delta':
      t.roundRaw += ev.text;
      setBubbleRaw(t.bubble, t.answerRaw + t.roundRaw);
      setStatus(t, '回答中…');
      break;
    case 'round_end':
      if (ev.has_tools) {
        if (t.roundRaw.trim()) {
          const nb = createTblk(t.traceEl, 'note');
          nb.icon = nb.head.children[0];
          nb.icon.textContent = '📝';
          nb.title.textContent = 'Model Assistant';
          nb.summary.textContent = oneLine(t.roundRaw, 60);
          nb.body.textContent = t.roundRaw;
        }
        t.roundRaw = '';
        setBubbleRaw(t.bubble, t.answerRaw);
      } else {
        t.answerRaw += t.roundRaw;
        t.roundRaw = '';
        setBubbleRaw(t.bubble, t.answerRaw);
      }
      break;
    case 'tool_call': {
      const tb = createTblk(t.traceEl, 'tool');
      tb.root.className = 'tblk tool running';
      tb.icon = tb.head.children[0];
      tb.icon.textContent = '🔧';
      tb.title.textContent = 'Tools';
      tb.name = ev.name || '';
      tb.args = ev.parameter !== undefined ? ev.parameter : (ev.args || '');  // 旧会话兼容
      tb.summary.textContent = oneLine(tb.name + ' · ' + tb.args, 60);
      tb.body.textContent = 'tool: ' + tb.name + '\\nparameter: ' + tb.args;
      t.steps += 1;
      t.pendingTools.push(tb);
      setStatus(t, '调用工具…');
      break;
    }
    case 'tool_result': {
      const tb = t.pendingTools.shift();
      if (tb) {
        const warn = typeof ev.exit_code === 'number' && ev.exit_code !== 0;
        tb.root.className = 'tblk tool ' + (ev.ok ? (warn ? 'warn' : 'ok') : 'err');
        tb.meta.textContent = warn
          ? '(' + formatMs(ev.duration_ms || 0) + ' ⚠ exit ' + ev.exit_code + ')'
          : '(' + formatMs(ev.duration_ms || 0) + ' ' + (ev.ok ? '✓' : '✗') + ')';
        tb.body.textContent = 'tool: ' + (tb.name || ev.name || '') + '\\nparameter: ' + (tb.args || '') + '\\noutput: ' + (ev.output || '');
        t.toolMs += ev.duration_ms || 0;
      }
      break;
    }
    case 'error': {
      const kind = ev.severity === 'warn' ? 'warn' : 'err';
      const eb = createTblk(t.traceEl, kind);
      eb.head.onclick = kind === 'warn' ? null : eb.head.onclick;
      eb.icon = eb.head.children[0];
      eb.icon.textContent = '⚠️';
      eb.title.textContent = ev.severity || 'error';
      eb.summary.textContent = oneLine(ev.message || ev.text || '', 60) + (ev.retryable ? '（可重试）' : '');
      eb.body.textContent = ev.message || ev.text || '';
      setStatus(t, '出错', 'err');
      break;
    }
    case 'retry': {
      const rb = createTblk(t.traceEl, 'retry');
      rb.head.onclick = null;
      rb.icon = rb.head.children[0];
      rb.icon.textContent = '↻';
      rb.title.textContent = '重试 ' + (ev.attempt || 1) + '/' + (ev.max || 3);
      rb.summary.textContent = oneLine(ev.message || '', 60);
      break;
    }
    case 'goal_start':
      setStatus(t, '目标执行中…');
      break;
    case 'goal_progress':
      setStatus(t, '推进中…');
      break;
    case 'goal_blocked': {
      const gb = createTblk(t.traceEl, 'warn');
      gb.head.onclick = null;
      gb.icon = gb.head.children[0];
      gb.icon.textContent = '⚠️';
      gb.title.textContent = '目标受阻';
      gb.summary.textContent = oneLine(ev.reason || '', 60);
      setStatus(t, '受阻', 'err');
      break;
    }
    case 'goal_end':
      setStatus(
        t,
        ev.status === 'blocked' ? '受阻' : '完成',
        ev.status === 'blocked' ? 'err' : 'done'
      );
      break;
    case 'todo': {
      const items = Array.isArray(ev.todos) ? ev.todos : [];
      const done = items.filter(function (x) { return x.status === 'completed'; }).length;
      if (!t.todoBlk) {
        t.todoBlk = createTblk(t.traceEl, 'todo');
        t.todoBlk.icon = t.todoBlk.head.children[0];
        t.todoBlk.icon.textContent = '📋';
        t.todoBlk.title.textContent = '任务清单';
      }
      t.todoBlk.meta.textContent = done + '/' + items.length;
      t.todoBlk.body.textContent = items.map(function (x) {
        const mark = x.status === 'completed' ? '☑' : (x.status === 'in_progress' ? '▶' : '☐');
        return mark + ' ' + x.content;
      }).join('\\n');
      break;
    }
    case 'subagent_start': {
      const sb = createTblk(t.traceEl, 'sub');
      sb.root.className = 'tblk sub running';
      sb.icon = sb.head.children[0];
      sb.icon.textContent = '🤖';
      sb.title.textContent = '子代理 · ' + (ev.name || '子任务');
      sb.summary.textContent = oneLine(ev.task || '', 60);
      sb.meta.textContent = '执行中…';
      t.pendingSubs.push(sb);
      break;
    }
    case 'subagent_end': {
      const sb = t.pendingSubs.shift();
      if (sb) {
        sb.root.className = 'tblk sub ' + (ev.ok ? 'ok' : 'err');
        sb.meta.textContent = ev.ok ? '✓' : '✗';
        sb.summary.textContent = oneLine(ev.summary || '', 60);
        sb.body.textContent = ev.summary || '';
      }
      break;
    }
    case 'compact': {
      const cb = createTblk(t.traceEl, 'note');
      cb.icon = cb.head.children[0];
      cb.icon.textContent = '📦';
      cb.title.textContent = '上下文压缩';
      cb.meta.textContent = (ev.before || 0) + ' → ' + (ev.after || 0) + ' tokens';
      cb.summary.textContent = oneLine(ev.summary || '', 60);
      cb.body.textContent = ev.summary || '';
      break;
    }
    case 'plan': {
      const pb = createTblk(t.traceEl, 'note');
      pb.icon = pb.head.children[0];
      pb.icon.textContent = '📐';
      pb.title.textContent = '执行计划';
      pb.summary.textContent = oneLine(ev.plan || '', 60);
      pb.body.textContent = ev.plan || '';
      break;
    }
    case 'skill_loaded': {
      const kb = createTblk(t.traceEl, 'note');
      kb.icon = kb.head.children[0];
      kb.icon.textContent = '📚';
      kb.title.textContent = '技能装载 · ' + (ev.name || '');
      kb.summary.textContent = oneLine(ev.description || '已装载技能，按其规范执行', 60);
      kb.body.textContent = (ev.description || '') + '\\n（技能仅在你显式指定时装载）';
      break;
    }
    case 'turn_end': {
      if (ev.interrupted) {
        const ib = createTblk(t.traceEl, 'warn');
        ib.head.onclick = null;
        ib.icon = ib.head.children[0];
        ib.icon.textContent = '⚠️';
        ib.title.textContent = '上次中断';
        ib.summary.textContent = '上次运行在此中断，未完成';
      }
      if (!t.answerRaw.trim() && !t.traceEvents.some(function (x) { return x.type === 'tool_result'; })) {
        setBubbleRaw(t.bubble, '（无回复）');
      }
      const groups = [];
      if (t.steps > 0) groups.push(t.steps + ' 步 · 工具 ' + formatMs(t.toolMs));
      const usage = ev.usage;
      if (usage && typeof usage.total_tokens === 'number' && usage.total_tokens > 0) {
        groups.push(usage.total_tokens + ' tokens');
      }
      if (groups.length && !t.statsEl) {
        t.statsEl = document.createElement('div');
        t.statsEl.className = 'turn-stats';
        t.statsEl.textContent = groups.join(' · ');
        t.traceEl.appendChild(t.statsEl);
      }
      setStatus(t, '完成', 'done');
      break;
    }
  }
}

function renderTraceFromEvents(traceEl, events) {
  const t = newTurnState(null, traceEl);
  events.forEach(function (ev) { handleEvent(ev, t); });
  // 回放兜底：未闭合的 running 块收尾标记
  if (t.think) {
    t.think.root.className = 'tblk think';
    t.think.summary.textContent = oneLine(t.thinkRaw, 60);
    t.think.meta.textContent = '(' + t.thinkRaw.length + ' 字)';
  }
  t.pendingTools.forEach(function (tb) {
    tb.root.className = 'tblk tool err';
    tb.meta.textContent = '（未完成）';
  });
  t.pendingSubs.forEach(function (sb) {
    sb.root.className = 'tblk sub err';
    sb.meta.textContent = '（未完成）';
  });
}

/* 中断轮次标记（对齐 DSH interrupted closer）：末轮 trace 无 turn_end 时补标记 */
function markInterruptedTurn() {
  const last = chatMessages[chatMessages.length - 1];
  if (!last || last.role !== 'agent' || !last.trace || !last.trace.length) return;
  const hasEnd = last.trace.some(function (e) { return e.type === 'turn_end'; });
  if (!hasEnd) {
    last.trace = last.trace.concat([{type: 'turn_end', text: '', interrupted: true}]);
  }
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

/* ---------- 斜杠命令（迭代 8 · 8.6：/goal /plan /chat） ---------- */
const CMD_ITEMS = [
  {cmd: '/goal', icon: '🎯', name: '/goal', desc: '目标模式：长任务自动续跑'},
  {cmd: '/plan', icon: '📐', name: '/plan', desc: '先制定计划再执行'},
  {cmd: '/skill', icon: '📚', name: '/skill', desc: '显式装载技能执行任务'},
  {cmd: '/skills', icon: '🗂', name: '/skills', desc: '浏览与管理技能'},
];

function parseCommand(text) {
  const t = text.trim();
  if (t === '/goal' || t.startsWith('/goal ')) {
    const rest = t === '/goal' ? '' : t.slice('/goal'.length).trim();
    return {cmd: 'goal', task: rest};
  }
  if (t === '/plan' || t.startsWith('/plan ')) {
    const rest = t === '/plan' ? '' : t.slice('/plan'.length).trim();
    return {cmd: 'plan', task: rest};
  }
  if (t === '/chat' || t.startsWith('/chat ')) {
    const rest = t === '/chat' ? '' : t.slice('/chat'.length).trim();
    return {cmd: 'chat', task: rest};
  }
  if (t === '/skills' || t.startsWith('/skills ')) {  // 先于 /skill 判断
    return {cmd: 'skills', task: t === '/skills' ? '' : t.slice('/skills'.length).trim()};
  }
  if (t === '/skill' || t.startsWith('/skill ')) {
    const rest = t === '/skill' ? '' : t.slice('/skill'.length).trim();
    return {cmd: 'skill', task: rest};
  }
  return {cmd: '', task: t};
}

function flashHint(input, text) {
  const old = input.placeholder;
  input.placeholder = text;
  setTimeout(function () { input.placeholder = old; }, 3000);
}

/* / 命令浮层：输入 / 弹出可选命令，↑↓ 导航、Enter 选择、Esc 关闭、点击插入 */
function buildCmdPop() {
  const pop = document.getElementById('cmd-pop');
  const input = document.getElementById('chat-input');
  if (!pop || !input) return;
  let selIdx = 0;
  const updateSel = function () {
    const items = pop.children;
    for (let i = 0; i < items.length; i++) {
      items[i].className = 'cmd-item' + (i === selIdx ? ' sel' : '');
    }
  };
  const render = function () {
    const v = input.value;
    if (v.startsWith('/') && !v.includes(' ') && !v.includes('\\n') && v.length <= 8) {
      const items = CMD_ITEMS.filter(function (it) { return it.cmd.indexOf(v) === 0; });
      if (items.length) {
        pop.innerHTML = '';
        selIdx = Math.min(selIdx, items.length - 1);
        items.forEach(function (it, i) {
          const row = document.createElement('div');
          row.className = 'cmd-item' + (i === selIdx ? ' sel' : '');
          const ic = document.createElement('span');
          ic.className = 'cmd-icon';
          ic.textContent = it.icon;
          const nm = document.createElement('span');
          nm.className = 'cmd-name';
          nm.textContent = it.cmd;
          const ds = document.createElement('span');
          ds.className = 'cmd-desc';
          ds.textContent = it.desc;
          row.appendChild(ic);
          row.appendChild(nm);
          row.appendChild(ds);
          row.onclick = function () {
            input.value = it.cmd + ' ';
            pop.classList.remove('open');
            input.focus();
          };
          pop.appendChild(row);
        });
        pop.classList.add('open');
        return;
      }
    }
    pop.classList.remove('open');
  };
  input.addEventListener('input', render);
  input.addEventListener('keydown', function (e) {
    const open = pop.classList.contains('open');
    const items = pop.children;
    if (open && e.key === 'ArrowDown') { e.preventDefault(); selIdx = Math.min(selIdx + 1, items.length - 1); updateSel(); }
    else if (open && e.key === 'ArrowUp') { e.preventDefault(); selIdx = Math.max(selIdx - 1, 0); updateSel(); }
    else if (open && e.key === 'Escape') { pop.classList.remove('open'); }
    else if (open && e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const sel = items[selIdx];
      if (sel) sel.onclick();
    }
    else if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendTask(); }
  });
  input.addEventListener('blur', function () {
    setTimeout(function () { pop.classList.remove('open'); }, 150);
  });
}

async function sendTask() {
  const input = document.getElementById('chat-input');
  const parsed = parseCommand(input.value);
  const cmd = parsed.cmd;
  if (cmd === 'skills') { input.value = ''; openSkillsPanel(); return; }
  let task = parsed.task;
  let skillParam = '';
  if (cmd === 'skill') {
    const sp = parsed.task.indexOf(' ');
    const name = sp === -1 ? parsed.task : parsed.task.slice(0, sp);
    const extra = sp === -1 ? '' : parsed.task.slice(sp + 1).trim();
    if (!name) { flashHint(input, '/skill 需要技能名，例如：/skill python-testing 写单测'); return; }
    skillParam = name;
    task = extra || ('请确认已装载技能 ' + name + '，并简要说明你将如何应用它');
  }
  const goalMode = cmd === 'goal';
  const planMode = cmd === 'plan';
  const chatCmd = cmd === 'chat';
  let mode = state.mode;
  if (chatCmd) mode = 'chat';
  if (goalMode || planMode || skillParam) mode = 'agent';  // 这三类命令仅 agent 模式
  if (!task) {
    if (goalMode) flashHint(input, '/goal 需要跟随任务，例如：/goal 实现用户登录功能');
    if (planMode) flashHint(input, '/plan 需要跟随任务，例如：/plan 实现用户登录功能');
    if (chatCmd) flashHint(input, '/chat 需要跟随问题，例如：/chat 解释什么是装饰器');
    return;
  }
  input.value = '';
  if (!chatMessages.some(m => m.role === 'user')) firstTask = task;
  chatMessages.push({role: 'user', raw: task});
  appendMsg('user', task);
  chatMessages.push({role: 'agent', raw: ''});
  const agent = appendAgentMsg();
  const idx = chatMessages.length - 1;
  await ensureSession(task);
  saveMessages();
  const es = new EventSource('/events?task=' + encodeURIComponent(task) + '&workdir=' + encodeURIComponent(state.workspace) + '&session=' + encodeURIComponent(currentSessionId || '') + '&mode=' + encodeURIComponent(mode) + (goalMode ? '&goal=1' : '') + (planMode ? '&plan=1' : '') + (skillParam ? '&skill=' + encodeURIComponent(skillParam) : ''));
  const t = newTurnState(agent.bubble, agent.traceEl);
  t.statusEl = agent.status;
  es.onmessage = function (e) {
    if (e.data === '[DONE]') {
      t.done = true;  // 正常结束标记：其后的 EOF onerror 不再误报断线
      es.close();
      chatMessages[idx].raw = t.answerRaw;
      chatMessages[idx].trace = t.traceEvents;
      setStatus(t, '完成', 'done');
      refreshFiles();
      saveMessages();
      if (firstTask) { autoRenameSession(firstTask); firstTask = null; }
      return;
    }
    let ev;
    try { ev = JSON.parse(e.data); } catch (err) { return; }
    handleEvent(ev, t);
    const h = document.getElementById('chat-history');
    h.scrollTop = h.scrollHeight;
  };
  es.onerror = function () {
    es.close();  // 防 EventSource 自动重连导致服务端重复运行任务
    if (t.done || t.connErr) return;  // 正常完成后的 EOF 或已提示过 → 忽略
    t.connErr = true;
    const eb = createTblk(t.traceEl, 'err');
    eb.icon = eb.head.children[0];
    eb.icon.textContent = '⚠️';
    eb.title.textContent = '连接中断';
    eb.summary.textContent = '流已停止，请重新发送任务';
    eb.body.textContent = 'SSE 连接中断，服务端任务已停止；请重新发送任务继续。';
    setStatus(t, '出错', 'err');
  };
}

/* ---------- 中央编辑器（Monaco，CDN；离线回退行号视图） ---------- */
let editorInited = false;
let monacoTimedOut = false;

function initEditor() {
  if (editorInited) return;
  editorInited = true;
  const host = document.getElementById('editor-host');
  if (!host) return;
  host.className = '';
  try {
    editor = monaco.editor.create(host, {
      value: currentFile ? currentFile.content : '',
      language: currentFile ? langOf(currentFile.name) : 'plaintext',
      theme: 'vs',
      automaticLayout: true,
      fontSize: 14,
      minimap: { enabled: false },
    });
    try {
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, function () { saveFile(); });
    } catch (e2) { /* 忽略 */ }
    // flex 容器中 automaticLayout 偶发失效：创建后与窗口变化时显式重排
    setTimeout(function () {
      try { if (editor) editor.layout(); } catch (e3) { /* 忽略 */ }
    }, 50);
    window.addEventListener('resize', function () {
      try { if (editor) editor.layout(); } catch (e3) { /* 忽略 */ }
    });
  } catch (e) {
    editor = null;
    fallbackEditor();
  }
}

function fallbackEditor() {
  if (editorInited && editor) return;
  editorInited = true;
  editor = null;
  const host = document.getElementById('editor-host');
  if (!host) return;
  host.className = 'file-view';
  if (currentFile) { renderFile(currentFile.content); }
  else { host.innerHTML = '<div class="placeholder">编辑器加载中或不可用（回退行号视图），点击左侧文件仍可查看</div>'; }
}

function ensureMonaco() {
  if (window.monaco) { initEditor(); return; }
  if (window.require && typeof window.require === 'function' && !monacoTimedOut) {
    // 8 秒超时兜底：CDN 过慢则回退行号视图，避免中间栏空白
    setTimeout(function () {
      if (!window.monaco && !editorInited) { monacoTimedOut = true; fallbackEditor(); }
    }, 8000);
    try {
      require(['vs/editor/editor.main'], function () { initEditor(); });
    } catch (e) {
      if (!editorInited) fallbackEditor();
    }
    return;
  }
  if (!editorInited) fallbackEditor();
}

function buildEditor() {
  document.getElementById('pane-center').innerHTML = `
    <div id="file-header">
      <span id="file-tab">—</span>
      <button id="file-save" onclick="saveFile()" title="保存修改（Ctrl+S）">保存</button>
    </div>
    <div id="editor-host"><div class="placeholder">点击左侧文件树查看代码</div></div>`;
  ensureMonaco();
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
      currentFile = { name: data.name, content: data.content };
      if (tab) { tab.textContent = data.name; tab.style.display = ''; }
      const saveBtn = document.getElementById('file-save');
      if (saveBtn) saveBtn.style.display = '';
      if (editor) {
        try {
          editor.setValue(data.content);
          monaco.editor.setModelLanguage(editor.getModel(), langOf(data.name));
        } catch (e) {
          editor.setValue(data.content);
        }
      } else {
        renderFile(data.content);
      }
    } else {
      if (tab) tab.style.display = 'none';
      const saveBtn = document.getElementById('file-save');
      if (saveBtn) saveBtn.style.display = 'none';
      const view = document.getElementById('editor-host');
      if (view) view.innerHTML = '<div class="placeholder">' + (data.error || '加载失败') + '</div>';
    }
  } catch (e) {
    const view = document.getElementById('editor-host');
    if (view) view.innerHTML = '<div class="placeholder">请求失败</div>';
  }
}

async function saveFile() {
  if (!currentFile) return;
  const content = editorContent();
  const btn = document.getElementById('file-save');
  const done = ok => {
    if (!btn) return;
    btn.textContent = ok ? '已保存 ✓' : '保存失败';
    btn.disabled = true;
    setTimeout(function () { btn.textContent = '保存'; btn.disabled = false; }, 1500);
  };
  try {
    const resp = await fetch('/save-file', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({workdir: state.workspace, path: currentFile.name, content: content}),
    });
    const data = await resp.json();
    if (data.ok) { currentFile.content = content; done(true); }
    else { done(false); }
  } catch (e) { done(false); }
}

function editorContent() {
  if (editor) {
    try { return editor.getValue(); } catch (e) { /* 回退 textarea */ }
  }
  const ta = document.getElementById('file-ta');
  return ta ? ta.value : '';
}

function renderFile(content) {
  const view = document.getElementById('editor-host');
  if (!view) return;
  view.className = 'file-view';
  view.innerHTML = '';
  const nums = document.createElement('div');
  nums.className = 'fv-nums';
  const ta = document.createElement('textarea');
  ta.className = 'fv-ta';
  ta.id = 'file-ta';
  ta.value = content;
  ta.spellcheck = false;
  const syncNums = function () {
    const n = ta.value.split('\\n').length;
    let out = '';
    for (let i = 1; i <= n; i++) out += i + '\\n';
    nums.textContent = out;
  };
  syncNums();
  ta.addEventListener('scroll', function () { nums.scrollTop = ta.scrollTop; });
  ta.addEventListener('input', syncNums);
  ta.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveFile(); }
  });
  view.appendChild(nums);
  view.appendChild(ta);
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

(async function boot() {
  initSplitters();
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


def _history_from_session(session: dict | None, task: str) -> list[dict[str, str]]:
    """把会话持久化消息转成 LLM 前置历史（同会话上下文互通）。

    规则：跳过空消息（raw 为空，如流式占位）；剔除「与当前任务内容相同的
    最后一条 user 消息」（前端已在发请求前保存当前任务，避免重复注入）。
    """
    if not session:
        return []
    saved = session.get("messages") or []
    last_match: int | None = None
    for i, m in enumerate(saved):
        if m.get("role") == "user" and (m.get("raw") or "").strip() == task:
            last_match = i
    history: list[dict[str, str]] = []
    for i, m in enumerate(saved):
        if i == last_match:
            continue
        role = m.get("role")
        raw = (m.get("raw") or "").strip()
        if not raw:
            continue
        if role == "user":
            history.append({"role": "user", "content": raw})
        elif role == "agent":
            history.append({"role": "assistant", "content": raw})
    return history


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


class _NullWriter:
    """Web 事件流模式下丢弃 stdout（输出全部走 emit 事件，避免双通道重复）。"""

    def write(self, text: str) -> int:
        return len(text)

    def flush(self) -> None:
        pass


class AgentHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler 约定命名
        if self.path == "/":
            data = INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")  # 防旧页缓存
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/events"):
            self._handle_events()
        elif self.path.startswith("/tree"):
            self._handle_tree()
        elif self.path.startswith("/file"):
            self._handle_file()
        elif self.path.startswith("/sessions"):
            self._handle_sessions_get()
        elif self.path.startswith("/skills"):
            self._handle_skills_get()
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

    def _handle_save_file(self) -> None:
        """保存工作区内文件（UTF-8；路径越界防护；允许子目录新建）。"""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            workdir = str(body.get("workdir") or self.server.workdir)
            rel = str(body.get("path") or "")
            content = str(body.get("content") or "")
            if not rel:
                raise ValueError("缺少 path")
            root = Path(workdir).resolve()
            if not root.is_dir():
                raise ValueError(f"工作区不存在：{workdir}")
            target = (root / rel).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"路径越界：{rel}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            result = {"ok": True, "path": rel, "name": target.name}
        except Exception as exc:  # noqa: BLE001
            result = {"ok": False, "error": str(exc)}
        self._write_json(result)

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
        session_id = (query.get("session") or [None])[0]
        goal_mode = (query.get("goal") or ["0"])[0] in ("1", "true")
        plan_mode = (query.get("plan") or ["0"])[0] in ("1", "true")
        chat_mode = (query.get("mode") or ["agent"])[0] == "chat"
        skill_names = [
            s.strip() for s in (query.get("skill") or [""])[0].split(",") if s.strip()
        ]
        session = None
        if session_id:
            try:
                session = self._sessions().get_session(session_id)
            except Exception:  # noqa: BLE001 - 会话读取失败按全新会话处理
                session = None
        history = _history_from_session(session, task)  # 同会话上下文互通
        # goal 恢复注入：上次目标未完成（open）时提示先验证副作用、只重试幂等操作
        resume_note = ""
        if session and (session.get("goal") or {}).get("status") == "open":
            summary = str((session.get("goal") or {}).get("summary") or "")[:200]
            resume_note = (
                "\n\n（此前目标未完成"
                + (f"，摘要：{summary}" if summary else "")
                + "。请先验证已完成的工作与副作用，仅重试幂等操作，再继续完成目标。）"
            )
        task_effective = task + resume_note
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        q: queue.Queue = queue.Queue()
        config = self.server.config

        def worker() -> None:
            try:
                with contextlib.redirect_stdout(_NullWriter()):
                    stream_cfg = dataclasses.replace(config, stream=True, goal=goal_mode)  # Web 恒流式
                    client = LLMClient(stream_cfg)
                    task_run = task_effective
                    run_tools = None  # agent 模式：全部工具
                    run_mode = "agent"
                    if chat_mode:
                        run_mode = "chat"
                        run_tools = tool_schemas_for(READ_ONLY_TOOL_NAMES)
                    # 技能：仅显式指定装载（skill 参数逗号分隔；未知名/模式不符容错忽略）
                    loaded_skills = []
                    if skill_names:
                        try:
                            skills_map = load_skills(workdir)
                            for nm in skill_names:
                                s = skills_map.get(nm)
                                if s is not None and run_mode in s.modes:
                                    loaded_skills.append(s)
                        except Exception:  # noqa: BLE001 - 技能加载失败按无技能继续
                            loaded_skills = []
                    if plan_mode:
                        try:
                            plan = make_plan(client, task_run)
                            if plan:
                                q.put({"type": "plan", "plan": plan, "text": ""})
                                task_run = f"{task_run}\n\n已制定的执行计划：\n{plan}\n请按计划逐步执行。"
                        except Exception:  # noqa: BLE001 - 计划失败按无计划继续
                            pass
                    result = run(
                        stream_cfg, task_run, workdir=workdir,
                        client=client, emit=q.put, history=history,
                        tools=run_tools, mode=run_mode,
                        skills=loaded_skills or None,
                    )
                    # goal 状态持久化（仅在 goal 模式或恢复 open 会话时写入，避免普通对话覆盖）
                    goal_open = (session or {}).get("goal", {}).get("status") == "open"
                    if session_id and session is not None and (goal_mode or goal_open):
                        try:
                            r = (result or "").strip()
                            status = "open"
                            if r.startswith("受阻"):
                                status = "blocked"
                            elif r.startswith("完成"):
                                status = "done"
                            self._sessions().update_goal(
                                session_id, {"status": status, "summary": r[:200]}
                            )
                        except Exception:  # noqa: BLE001 - 状态持久化失败不影响主流程
                            pass
            except Exception as exc:  # noqa: BLE001 - 错误推送给前端
                q.put({"type": "error", "severity": "error", "message": str(exc), "text": f"错误：{exc}"})
            finally:
                q.put(None)  # 结束哨兵

        threading.Thread(target=worker, daemon=True).start()
        try:
            while True:
                item = q.get()
                if item is None:
                    break
                try:
                    payload = json.dumps(item, ensure_ascii=False)
                except TypeError:  # 防御：事件不可序列化时降级为错误帧，避免流中断
                    payload = json.dumps(
                        {"type": "error", "severity": "error", "message": "事件序列化失败", "text": ""},
                        ensure_ascii=False,
                    )
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
        elif self.path.startswith("/save-file"):
            self._handle_save_file()
        elif self.path.startswith("/sessions"):
            self._handle_sessions_post()
        elif self.path.startswith("/skills"):
            self._handle_skills_post()
        else:
            self.send_error(404)

    def do_PUT(self):  # noqa: N802 - 技能更新（PUT /skills/<name>）
        parts = [p for p in urllib.parse.urlparse(self.path).path.split("/") if p]
        if len(parts) == 2 and parts[0] == "skills":
            self._handle_skills_post(require_existing=True)
        else:
            self.send_error(404)

    def do_DELETE(self):  # noqa: N802 - 会话删除 + 技能删除
        parts = [p for p in urllib.parse.urlparse(self.path).path.split("/") if p]
        if len(parts) == 2 and parts[0] == "sessions":
            ok = self._sessions().delete_session(parts[1])
            result = {"ok": True} if ok else {"ok": False, "error": f"会话不存在：{parts[1]}"}
        elif len(parts) == 2 and parts[0] == "skills":
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            workdir = (query.get("workdir") or [None])[0] or self.server.workdir
            ok = delete_workspace_skill(workdir, parts[1])
            result = (
                {"ok": True}
                if ok
                else {"ok": False, "error": f"技能不存在或为只读（仅工作区级可删除）：{parts[1]}"}
            )
        else:
            self.send_error(404)
            return
        data = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ---------- 会话端点 ----------
    def _sessions(self) -> SessionStore:
        if not hasattr(self.server, "sessions"):
            self.server.sessions = SessionStore()
        return self.server.sessions

    def _write_json(self, result: dict) -> None:
        data = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_sessions_get(self) -> None:
        parts = [p for p in urllib.parse.urlparse(self.path).path.split("/") if p]
        try:
            if len(parts) == 1:
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                workspace = (query.get("workspace") or [None])[0]
                result = {"ok": True, "sessions": self._sessions().list_sessions(workspace)}
            elif len(parts) == 2:
                session = self._sessions().get_session(parts[1])
                result = (
                    {"ok": True, "session": session}
                    if session is not None
                    else {"ok": False, "error": f"会话不存在：{parts[1]}"}
                )
            else:
                self.send_error(404)
                return
        except Exception as exc:  # noqa: BLE001
            result = {"ok": False, "error": str(exc)}
        self._write_json(result)

    def _handle_sessions_post(self) -> None:
        parts = [p for p in urllib.parse.urlparse(self.path).path.split("/") if p]
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        try:
            if len(parts) == 1:  # POST /sessions 新建
                workspace = str(body.get("workspace") or self.server.workdir)
                name = str(body.get("name") or "")
                result = {"ok": True, "session": self._sessions().create_session(workspace, name)}
            elif len(parts) == 3 and parts[2] == "messages":  # POST /sessions/<id>/messages
                messages = body.get("messages")
                if not isinstance(messages, list):
                    raise ValueError("messages 应为列表")
                session = self._sessions().save_messages(parts[1], messages)
                result = (
                    {"ok": True, "session": session}
                    if session is not None
                    else {"ok": False, "error": f"会话不存在：{parts[1]}"}
                )
            elif len(parts) == 2:  # POST /sessions/<id> 重命名
                name = str(body.get("name") or "")
                session = self._sessions().rename_session(parts[1], name)
                result = (
                    {"ok": True, "session": session}
                    if session is not None
                    else {"ok": False, "error": f"会话不存在：{parts[1]}"}
                )
            else:
                self.send_error(404)
                return
        except Exception as exc:  # noqa: BLE001
            result = {"ok": False, "error": str(exc)}
        self._write_json(result)

    # ---------- 技能端点（迭代 9 · 9.3：工作区级 CRUD + 只读标注） ----------
    def _handle_skills_get(self) -> None:
        """GET /skills?workdir= 技能列表（含 source 只读标注）。"""
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        workdir = (query.get("workdir") or [None])[0] or self.server.workdir
        try:
            result = {"ok": True, "skills": skill_summary(load_skills(workdir))}
        except Exception as exc:  # noqa: BLE001
            result = {"ok": False, "error": str(exc)}
        self._write_json(result)

    @staticmethod
    def _parse_skill_body(body: dict) -> dict:
        """解析技能表单字段（POST 新建 / PUT 更新共用）。"""
        keywords = body.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.replace("，", ",").split(",") if k.strip()]
        modes = body.get("modes") or []
        if isinstance(modes, str):
            modes = [m.strip() for m in modes.replace("，", ",").split(",") if m.strip()]
        return {
            "description": str(body.get("description") or "").strip(),
            "keywords": keywords if isinstance(keywords, list) else [],
            "modes": modes if isinstance(modes, list) else [],
            "body": str(body.get("body") or ""),
        }

    def _handle_skills_post(self, require_existing: bool = False) -> None:
        """POST /skills 新建；POST/PUT /skills/<name> 更新（仅工作区级）。"""
        parts = [p for p in urllib.parse.urlparse(self.path).path.split("/") if p]
        length = int(self.headers.get("Content-Length", 0))
        raw = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(raw, dict):
            raw = {}
        workdir = str(raw.get("workdir") or self.server.workdir)
        fields = self._parse_skill_body(raw)
        try:
            if require_existing and len(parts) != 2:
                raise ValueError("PUT 仅支持 /skills/<name> 更新")
            if len(parts) == 1:  # POST /skills 新建
                name = str(raw.get("name") or "").strip()
                skill = save_workspace_skill(workdir, name, **fields)
                result = {"ok": True, "skill": skill}
            elif len(parts) == 2:  # POST/PUT /skills/<name> 更新
                skill = update_workspace_skill(workdir, parts[1], **fields)
                result = {"ok": True, "skill": skill}
            else:
                self.send_error(404)
                return
        except Exception as exc:  # noqa: BLE001
            result = {"ok": False, "error": str(exc)}
        self._write_json(result)

    def log_message(self, format, *args):  # noqa: A002 - 静默访问日志
        pass


def serve(config: Config, workdir: str = ".", host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), AgentHandler)
    server.config = config
    server.workdir = workdir
    server.sessions = SessionStore()
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
