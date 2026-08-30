"""会话持久化：服务端 JSON 文件存储。

布局（DSH 同构简化）：data/sessions/<ws-slug>/<id>.json + 根 index.json。
会话模型：{"id", "name", "workspace", "created_at", "updated_at", "messages"}
线程安全（RLock）；会话数据不入库（见 .gitignore 的 data/）。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = Path("data") / "sessions"


def _normalize_ws(path: str) -> str:
    """工作区路径归一化：反斜杠→正斜杠、去尾分隔符；Windows 忽略大小写。"""
    p = str(path or "").replace("\\", "/").rstrip("/")
    if os.name == "nt":
        p = p.casefold()
    return p


def _ws_slug(workspace: str) -> str:
    """把工作区路径转成安全的目录名（可读 + 8 位 md5 防碰撞）。"""
    n = _normalize_ws(workspace)
    if not n:
        return "_no-ws"
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", n)[:100]
    digest = hashlib.md5(n.encode("utf-8")).hexdigest()[:8]
    return f"{safe}~{digest}"


class SessionStore:
    """会话存储：单文件一会话 + 索引文件。"""

    def __init__(self, data_dir: str | Path = DEFAULT_DATA_DIR):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._migrate_flat()  # 旧版平铺布局 → 工作区分层布局

    # ---------- 路径与索引 ----------
    def _index_path(self) -> Path:
        return self._dir / "index.json"

    def _ws_dir(self, workspace: str) -> Path:
        return self._dir / _ws_slug(workspace)

    def _session_path(self, session_id: str, workspace: str | None = None) -> Path:
        """会话文件路径：优先旧版平铺文件（兼容），否则按工作区目录定位。"""
        flat = self._dir / f"{session_id}.json"
        if flat.is_file():
            return flat
        if workspace is None:
            for e in self._read_index():
                if e.get("id") == session_id:
                    workspace = e.get("workspace", "")
                    break
        return self._ws_dir(workspace or "") / f"{session_id}.json"

    def _migrate_flat(self) -> None:
        """把旧版平铺 <id>.json 迁移到 <ws-slug>/<id>.json（保守：失败保留旧文件）。"""
        with self._lock:
            for p in self._dir.glob("*.json"):
                if p.name == "index.json":
                    continue
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                sid = str(data.get("id") or "")
                if not sid or f"{sid}.json" != p.name:
                    continue
                dst = self._ws_dir(data.get("workspace", "")) / f"{sid}.json"
                if dst.exists():
                    try:
                        p.unlink()
                    except OSError:
                        pass
                    continue
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    p.rename(dst)
                except OSError:
                    pass  # 迁移失败保留旧文件，读取仍走兼容路径

    def _read_index(self) -> list[dict[str, Any]]:
        p = self._index_path()
        if not p.is_file():
            return []
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return data.get("sessions", []) if isinstance(data, dict) else []

    def _write_index(self, entries: list[dict[str, Any]]) -> None:
        self._index_path().write_text(
            json.dumps({"sessions": entries}, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _write_session(self, session: dict[str, Any]) -> None:
        p = self._session_path(str(session["id"]), session.get("workspace", ""))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _sync_index(self, session: dict[str, Any]) -> None:
        entry = {
            "id": session["id"],
            "name": session["name"],
            "workspace": session["workspace"],
            "updated_at": session["updated_at"],
        }
        entries = [e for e in self._read_index() if e.get("id") != session["id"]]
        entries.append(entry)
        self._write_index(entries)

    # ---------- CRUD ----------
    def list_sessions(self, workspace: str | None = None) -> list[dict[str, Any]]:
        """会话索引列表，按最近更新倒序。

        workspace 给定时仅返回属于该工作区的会话（路径归一化比较）；
        为 None 时返回全部（兼容旧调用）。
        """
        with self._lock:
            entries = self._read_index()
        if workspace is not None:
            target = _normalize_ws(workspace)
            entries = [
                e for e in entries if _normalize_ws(e.get("workspace", "")) == target
            ]
        entries.sort(key=lambda s: s.get("updated_at", 0), reverse=True)
        return entries

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            p = self._session_path(session_id)
            if not p.is_file():
                return None
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return None

    def _id_exists(self, session_id: str) -> bool:
        """会话 id 全局唯一检查（平铺 + 索引 + 各工作区目录）。"""
        if (self._dir / f"{session_id}.json").is_file():
            return True
        if any(e.get("id") == session_id for e in self._read_index()):
            return True
        return any(
            d.is_dir() and (d / f"{session_id}.json").is_file()
            for d in self._dir.iterdir()
        )

    def create_session(self, workspace: str, name: str = "") -> dict[str, Any]:
        with self._lock:
            session_id = "s" + datetime.now().strftime("%Y%m%d%H%M%S")
            while self._id_exists(session_id):
                session_id += "x"
            session = {
                "id": session_id,
                "name": (name or "新会话").replace("\n", " ").strip()[:24],
                "workspace": workspace,
                "created_at": time.time(),
                "updated_at": time.time(),
                "messages": [],
            }
            self._write_session(session)
            self._sync_index(session)
            return session

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            p = self._session_path(session_id)
            if not p.is_file():
                return False
            p.unlink()
            self._write_index([e for e in self._read_index() if e.get("id") != session_id])
            return True

    def rename_session(self, session_id: str, name: str) -> dict[str, Any] | None:
        with self._lock:
            session = self.get_session(session_id)
            if session is None:
                return None
            session["name"] = name.replace("\n", " ").strip()[:24] or "新会话"
            session["updated_at"] = time.time()
            self._write_session(session)
            self._sync_index(session)
            return session

    def save_messages(self, session_id: str, messages: list[dict[str, Any]]) -> dict[str, Any] | None:
        """全量保存会话消息并刷新索引（updated_at）。"""
        with self._lock:
            session = self.get_session(session_id)
            if session is None:
                return None
            session["messages"] = messages
            session["updated_at"] = time.time()
            self._write_session(session)
            self._sync_index(session)
            return session
