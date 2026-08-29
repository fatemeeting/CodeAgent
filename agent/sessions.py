"""会话持久化：服务端 JSON 文件存储（data/sessions/<id>.json + index.json）。

会话模型：{"id", "name", "workspace", "created_at", "updated_at", "messages"}
线程安全（RLock）；会话数据不入库（见 .gitignore 的 data/）。
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = Path("data") / "sessions"


class SessionStore:
    """会话存储：单文件一会话 + 索引文件。"""

    def __init__(self, data_dir: str | Path = DEFAULT_DATA_DIR):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    # ---------- 路径与索引 ----------
    def _index_path(self) -> Path:
        return self._dir / "index.json"

    def _session_path(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.json"

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
        self._session_path(str(session["id"])).write_text(
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
    def list_sessions(self) -> list[dict[str, Any]]:
        """会话索引列表，按最近更新倒序。"""
        with self._lock:
            entries = self._read_index()
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

    def create_session(self, workspace: str, name: str = "") -> dict[str, Any]:
        with self._lock:
            session_id = "s" + datetime.now().strftime("%Y%m%d%H%M%S")
            while self._session_path(session_id).is_file():
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
